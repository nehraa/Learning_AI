"""
Learning Plan Parser
Parses the daily_3hr_plan.md file and extracts structured learning data
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LearningPlanParser:
    """
    Parses daily_3hr_plan.md and extracts structured learning schedule
    """
    
    def __init__(self, plan_file: str = "daily_3hr_plan.md"):
        """
        Initialize parser
        
        Args:
            plan_file: Path to the learning plan markdown file
        """
        self.plan_file = Path(plan_file)
        if not self.plan_file.exists():
            # Try relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.plan_file = project_root / plan_file
        
        if not self.plan_file.exists():
            logger.error(f"Learning plan file not found: {plan_file}")
            self.content = None
        else:
            logger.info(f"Loading learning plan from: {self.plan_file}")
            self.content = self.plan_file.read_text(encoding='utf-8')
    
    def parse_overview(self) -> Dict:
        """
        Parse the plan overview section
        
        Returns:
            Dict with overview metadata
        """
        if not self.content:
            return {}
        
        overview = {
            'total_weeks': 52,
            'daily_hours': 3,
            'total_hours': 1100,
            'structure': 'micro-topic per day',
            'has_weekly_quiz': True
        }
        
        # Extract duration
        duration_match = re.search(r'\*\*Duration\*\*:\s*(\d+)\s*weeks?', self.content)
        if duration_match:
            overview['total_weeks'] = int(duration_match.group(1))
        
        # Extract daily time
        time_match = re.search(r'\*\*Daily Time\*\*:\s*(\d+)\s*hours?', self.content)
        if time_match:
            overview['daily_hours'] = int(time_match.group(1))
        
        # Extract total hours
        total_match = re.search(r'\*\*Total Hours\*\*:\s*~?(\d+)', self.content)
        if total_match:
            overview['total_hours'] = int(total_match.group(1))
        
        logger.info(f"Parsed plan overview: {overview['total_weeks']} weeks, {overview['daily_hours']} hrs/day")
        return overview
    
    def parse_day(self, week_num: int, day_num: int) -> Optional[Dict]:
        """
        Parse a specific day's content
        
        Args:
            week_num: Week number (1-52)
            day_num: Day number within week (1-7)
        
        Returns:
            Dict with day's learning plan or None if not found
        """
        if not self.content:
            return None
        
        # Try to find day section
        # Format: ### DAY X (Mon Dec 15) — Topic — 3 HOURS
        day_pattern = rf'### DAY \d+ \([^)]+\) — ([^—]+) — (\d+) HOURS'
        
        # Calculate absolute day number
        abs_day = (week_num - 1) * 7 + day_num
        
        # Find all day sections
        day_matches = list(re.finditer(day_pattern, self.content))
        
        if abs_day <= len(day_matches):
            match = day_matches[abs_day - 1]
            topic = match.group(1).strip()
            hours = int(match.group(2))
            
            # Extract content between this day and next day
            start_pos = match.start()
            if abs_day < len(day_matches):
                end_pos = day_matches[abs_day].start()
            else:
                # Last day - go to end or next major section
                end_pos = len(self.content)
            
            day_content = self.content[start_pos:end_pos]
            
            # Parse learning objectives
            objectives = []
            obj_match = re.search(r'\*\*Learning Objectives:\*\*(.*?)(?=\*\*|###|$)', 
                                 day_content, re.DOTALL)
            if obj_match:
                obj_text = obj_match.group(1)
                objectives = [line.strip('- ').strip() 
                            for line in obj_text.split('\n') 
                            if line.strip().startswith('-')]
            
            # Parse time breakdown
            time_breakdown = {}
            breakdown_match = re.search(r'\*\*Time Breakdown:\*\*(.*?)(?=\*\*|###|$)',
                                       day_content, re.DOTALL)
            if breakdown_match:
                breakdown_text = breakdown_match.group(1)
                # Parse lines like: - **0:00-0:45 (45 min)**: Description
                time_lines = re.findall(r'-\s*\*\*(\d+:\d+)-(\d+:\d+)\s*\((\d+)\s*min\)\*\*:\s*(.+)',
                                       breakdown_text)
                for start_time, end_time, duration, description in time_lines:
                    time_breakdown[f"{start_time}-{end_time}"] = {
                        'duration_min': int(duration),
                        'description': description.strip()
                    }
            
            # Parse mini-quiz
            quiz_questions = []
            quiz_match = re.search(r'\*\*Mini-Quiz Questions:\*\*(.*?)(?=\*\*|###|$)',
                                  day_content, re.DOTALL)
            if quiz_match:
                quiz_text = quiz_match.group(1)
                questions = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n\*\*|$)', 
                                      quiz_text, re.DOTALL)
                quiz_questions = [q.strip() for q in questions if q.strip()]
            
            # Parse resources
            resources = []
            res_match = re.search(r'\*\*Resources Needed:\*\*(.*?)(?=\*\*|###|$)',
                                 day_content, re.DOTALL)
            if res_match:
                res_text = res_match.group(1)
                resources = [line.strip('- ').strip() 
                           for line in res_text.split('\n') 
                           if line.strip().startswith('-')]
            
            day_plan = {
                'week': week_num,
                'day': day_num,
                'absolute_day': abs_day,
                'topic': topic,
                'hours': hours,
                'learning_objectives': objectives,
                'time_breakdown': time_breakdown,
                'resources': resources,
                'quiz_questions': quiz_questions,
                'completed': False
            }
            
            logger.debug(f"Parsed Day {abs_day}: {topic}")
            return day_plan
        
        return None
    
    def parse_week(self, week_num: int) -> Dict:
        """
        Parse an entire week's content
        
        Args:
            week_num: Week number (1-52)
        
        Returns:
            Dict with week's learning plan
        """
        week_plan = {
            'week_number': week_num,
            'days': [],
            'focus_area': None,
            'comprehensive_quiz': None
        }
        
        # Parse each day in the week
        for day in range(1, 8):  # 7 days per week
            day_plan = self.parse_day(week_num, day)
            if day_plan:
                week_plan['days'].append(day_plan)
        
        # Try to extract week focus area
        week_pattern = rf'## WEEK {week_num}:?\s*([^\n]+)'
        week_match = re.search(week_pattern, self.content, re.IGNORECASE)
        if week_match:
            week_plan['focus_area'] = week_match.group(1).strip()
        
        logger.info(f"Parsed Week {week_num}: {week_plan['focus_area']}")
        return week_plan
    
    def get_current_day_plan(self, start_date: Optional[datetime] = None) -> Optional[Dict]:
        """
        Get the plan for today based on start date
        
        Args:
            start_date: When the plan started (default: first day in plan)
        
        Returns:
            Today's learning plan or None
        """
        if not start_date:
            # Try to extract start date from plan
            # Format: DAY 1 (Mon Dec 15)
            first_day_match = re.search(r'DAY 1 \(([^)]+)\)', self.content)
            if first_day_match:
                date_str = first_day_match.group(1)
                try:
                    # Parse date (e.g., "Mon Dec 15")
                    year = datetime.now().year
                    start_date = datetime.strptime(f"{date_str} {year}", "%a %b %d %Y")
                except:
                    start_date = datetime.now()
            else:
                start_date = datetime.now()
        
        # Calculate which day we're on
        days_elapsed = (datetime.now() - start_date).days
        current_week = (days_elapsed // 7) + 1
        current_day = (days_elapsed % 7) + 1
        
        logger.info(f"Current position: Week {current_week}, Day {current_day}")
        return self.parse_day(current_week, current_day)
    
    def get_total_hours_target(self) -> int:
        """Get the total hours target for the learning plan"""
        overview = self.parse_overview()
        return overview.get('total_hours', 1100)
    
    def get_daily_hours_target(self) -> float:
        """Get the daily hours target"""
        overview = self.parse_overview()
        return float(overview.get('daily_hours', 3))
    
    def export_to_json(self) -> Dict:
        """
        Export the entire plan as a JSON structure
        
        Returns:
            Complete plan as nested dict
        """
        plan = {
            'overview': self.parse_overview(),
            'weeks': []
        }
        
        # Parse all weeks (limit to reasonable number for performance)
        for week in range(1, 53):  # 52 weeks
            week_plan = self.parse_week(week)
            if week_plan['days']:  # Only include weeks with actual content
                plan['weeks'].append(week_plan)
            else:
                break  # Stop when we run out of content
        
        logger.info(f"Exported plan: {len(plan['weeks'])} weeks")
        return plan


if __name__ == "__main__":
    # Test parser
    logging.basicConfig(level=logging.INFO)
    
    parser = LearningPlanParser("daily_3hr_plan.md")
    
    # Parse overview
    overview = parser.parse_overview()
    print(f"\n📊 Plan Overview:")
    print(f"  Duration: {overview['total_weeks']} weeks")
    print(f"  Daily Time: {overview['daily_hours']} hours")
    print(f"  Total Hours: {overview['total_hours']}")
    
    # Parse first day
    day1 = parser.parse_day(1, 1)
    if day1:
        print(f"\n📅 Day 1: {day1['topic']}")
        print(f"  Objectives: {len(day1['learning_objectives'])}")
        print(f"  Time Blocks: {len(day1['time_breakdown'])}")
        print(f"  Quiz Questions: {len(day1['quiz_questions'])}")
    
    # Get current day
    current = parser.get_current_day_plan()
    if current:
        print(f"\n✅ Current Day (Week {current['week']}, Day {current['day']})")
        print(f"  Topic: {current['topic']}")
