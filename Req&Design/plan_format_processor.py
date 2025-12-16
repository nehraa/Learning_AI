"""
Plan Format Processor - Handles multiple plan detail levels

This component accepts plans in various formats:
1. Ultra-detailed (52-week, 3hr daily breakdown like the QM example)
2. High-level (just topics + rough timeline)
3. Mixed (some weeks detailed, others high-level)
4. Natural language (just text description)

And normalizes them into a standard internal format that the system can execute.
"""

import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from anthropic import Anthropic

@dataclass
class PlanDay:
    day_number: int
    date: Optional[datetime] = None
    micro_topic: str = ""
    learning_objectives: List[str] = field(default_factory=list)
    time_breakdown: Dict[str, str] = field(default_factory=dict)
    resources: List[Dict] = field(default_factory=list)
    mini_quiz: List[Dict] = field(default_factory=list)
    estimated_hours: float = 3.0
    difficulty: int = 3  # 1-5

@dataclass
class PlanWeek:
    week_number: int
    theme: str
    days: List[PlanDay]
    weekly_quiz: List[Dict] = field(default_factory=list)
    capstone_project: Optional[str] = None

@dataclass
class LearningPlan:
    id: str
    topic: str
    format_type: str  # "ultra_detailed" | "high_level" | "mixed" | "natural"
    weeks: List[PlanWeek]
    total_weeks: int
    daily_hours: float
    prerequisite_graph: Dict[str, List[str]] = field(default_factory=dict)
    milestones: List[Dict] = field(default_factory=list)

class PlanFormatProcessor:
    """
    Processes and normalizes different plan formats.
    """
    
    def __init__(self, anthropic_key: str):
        self.client = Anthropic(api_key=anthropic_key)
        
    def process_plan(self, raw_plan: str | dict, format_hint: str = "auto") -> LearningPlan:
        """
        Main entry: takes any format, returns normalized LearningPlan.
        
        Args:
            raw_plan: Can be:
                - Dict (JSON plan from PlanGeneratorAI)
                - Markdown string (like the 52-week example)
                - Plain text description
            format_hint: "auto" | "ultra_detailed" | "high_level" | "natural"
        
        Returns:
            Normalized LearningPlan
        """
        
        # Detect format if auto
        if format_hint == "auto":
            format_hint = self._detect_format(raw_plan)
        
        # Route to appropriate processor
        if format_hint == "ultra_detailed":
            return self._process_ultra_detailed(raw_plan)
        elif format_hint == "high_level":
            return self._process_high_level(raw_plan)
        elif format_hint == "natural":
            return self._process_natural_language(raw_plan)
        elif format_hint == "mixed":
            return self._process_mixed(raw_plan)
        else:
            raise ValueError(f"Unknown format: {format_hint}")
    
    def _detect_format(self, raw_plan) -> str:
        """
        Auto-detect plan format.
        """
        
        if isinstance(raw_plan, dict):
            # Check if has detailed daily breakdowns
            if 'weeks' in raw_plan:
                first_week = raw_plan['weeks'][0]
                if 'days' in first_week:
                    first_day = first_week['days'][0]
                    if 'time_breakdown' in first_day:
                        return "ultra_detailed"
            return "high_level"
        
        elif isinstance(raw_plan, str):
            # Check for ultra-detailed markers
            if re.search(r'\d{2}:\d{2}-\d{2}:\d{2}', raw_plan):  # Time slots
                return "ultra_detailed"
            
            # Check for high-level structure
            if re.search(r'Week \d+:', raw_plan, re.IGNORECASE):
                return "high_level"
            
            # Default to natural language
            return "natural"
        
        return "high_level"
    
    def _process_ultra_detailed(self, raw_plan) -> LearningPlan:
        """
        Process ultra-detailed plans (like the 52-week QM example).
        
        Input format:
        - Markdown with ## WEEK N: heading
        - ### DAY N (Date) — Topic — 3 HOURS
        - **Time Breakdown:** with exact slots
        - **Mini-Quiz Questions:** list
        - **Resources Needed:** list
        """
        
        if isinstance(raw_plan, dict):
            # Already structured - just validate and wrap
            return self._wrap_json_plan(raw_plan)
        
        # Parse Markdown
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Extract topic from title
        topic_match = re.search(r'# YOUR \d+-WEEK.*?PLAN[^\n]*\n## (.*)', raw_plan)
        topic = topic_match.group(1).strip() if topic_match else "Unknown Topic"
        
        weeks = []
        
        # Split by weeks
        week_sections = re.split(r'## WEEK (\d+):', raw_plan)[1:]  # Skip header
        
        for i in range(0, len(week_sections), 2):
            week_num = int(week_sections[i])
            week_content = week_sections[i + 1]
            
            # Extract theme
            theme_match = re.search(r'^[^\n]+', week_content)
            theme = theme_match.group(0).strip() if theme_match else f"Week {week_num}"
            
            # Parse days
            days = []
            day_sections = re.split(r'### DAY (\d+)', week_content)[1:]
            
            for j in range(0, len(day_sections), 2):
                day_num = int(day_sections[j])
                day_content = day_sections[j + 1]
                
                # Extract micro-topic
                topic_match = re.search(r'—\s*([^—]+)\s*—', day_content)
                micro_topic = topic_match.group(1).strip() if topic_match else ""
                
                # Extract learning objectives
                objectives_match = re.search(
                    r'\*\*Learning Objectives:\*\*\s*\n((?:- .+\n?)+)', 
                    day_content
                )
                objectives = []
                if objectives_match:
                    objectives = [
                        line.strip('- ').strip() 
                        for line in objectives_match.group(1).split('\n') 
                        if line.strip().startswith('-')
                    ]
                
                # Extract time breakdown
                time_breakdown = {}
                time_match = re.search(
                    r'\*\*Time Breakdown:\*\*\s*\n((?:- \*\*\d{1,2}:\d{2}-\d{1,2}:\d{2}.*?\n?)+)',
                    day_content
                )
                if time_match:
                    for line in time_match.group(1).split('\n'):
                        if '**' in line:
                            parts = line.split('**')
                            if len(parts) >= 3:
                                time_slot = parts[1]
                                activity = parts[2].strip(': ')
                                time_breakdown[time_slot] = activity
                
                # Extract mini-quiz
                quiz = []
                quiz_match = re.search(
                    r'\*\*Mini-Quiz Questions:\*\*\s*\n((?:\d+\. .+\n?)+)',
                    day_content
                )
                if quiz_match:
                    questions = [
                        line.strip('0123456789. ').strip() 
                        for line in quiz_match.group(1).split('\n')
                        if re.match(r'^\d+\.', line.strip())
                    ]
                    quiz = [{'question': q, 'answer': '', 'difficulty': 'medium'} for q in questions]
                
                # Create PlanDay
                day = PlanDay(
                    day_number=day_num,
                    micro_topic=micro_topic,
                    learning_objectives=objectives,
                    time_breakdown=time_breakdown,
                    mini_quiz=quiz,
                    estimated_hours=3.0
                )
                
                days.append(day)
            
            # Create PlanWeek
            week = PlanWeek(
                week_number=week_num,
                theme=theme,
                days=days
            )
            
            weeks.append(week)
        
        return LearningPlan(
            id=plan_id,
            topic=topic,
            format_type="ultra_detailed",
            weeks=weeks,
            total_weeks=len(weeks),
            daily_hours=3.0
        )
    
    def _process_high_level(self, raw_plan) -> LearningPlan:
        """
        Process high-level plans (just topics, no daily breakdown).
        
        Input format:
        - "Week 1: Topic A"
        - "Week 2: Topic B"
        
        Output:
        - Expands each week into 7 days with AI-generated breakdown
        """
        
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Parse weekly topics
        if isinstance(raw_plan, str):
            week_lines = [
                line for line in raw_plan.split('\n') 
                if re.match(r'Week \d+:', line, re.IGNORECASE)
            ]
            
            topic = "Learning Plan"  # Extract from context or ask user
            
            weeks = []
            for line in week_lines:
                match = re.match(r'Week (\d+):\s*(.+)', line, re.IGNORECASE)
                if match:
                    week_num = int(match.group(1))
                    theme = match.group(2).strip()
                    
                    # Expand into days using AI
                    days = self._expand_week_to_days(theme, week_num)
                    
                    week = PlanWeek(
                        week_number=week_num,
                        theme=theme,
                        days=days
                    )
                    
                    weeks.append(week)
        
        elif isinstance(raw_plan, dict):
            # Extract from structured dict
            weeks = raw_plan.get('weeks', [])
            # ... similar processing
        
        return LearningPlan(
            id=plan_id,
            topic=topic,
            format_type="high_level",
            weeks=weeks,
            total_weeks=len(weeks),
            daily_hours=3.0
        )
    
    def _process_natural_language(self, raw_plan: str) -> LearningPlan:
        """
        Process natural language descriptions.
        
        Input:
        - "I want to learn philosophy, focusing on phenomenology and ethics"
        
        Output:
        - Full structured plan using PlanGeneratorAI
        """
        
        # Use Claude to extract intent
        prompt = f"""
User said: "{raw_plan}"

Extract:
1. Topic
2. Subtopics (if mentioned)
3. Timeline preference
4. Any other constraints

Output JSON:
{{
  "topic": "...",
  "subtopics": ["...", "..."],
  "timeline_weeks": 52,
  "daily_hours": 3,
  "constraints": ["..."]
}}
"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        extracted = json.loads(response.content[0].text)
        
        # Now use PlanGeneratorAI with extracted info
        from rfai.ai.plan_generator import PlanGeneratorAI
        
        generator = PlanGeneratorAI(self.client.api_key)
        
        plan = generator.generate_plan(
            topic=extracted['topic'],
            user_context={
                'time_available': f"{extracted.get('daily_hours', 3)} hours/day",
                'timeline': f"{extracted.get('timeline_weeks', 52)} weeks",
                'subtopics': extracted.get('subtopics', [])
            }
        )
        
        return plan
    
    def _expand_week_to_days(self, week_theme: str, week_num: int) -> List[PlanDay]:
        """
        Use AI to expand a weekly theme into 7 daily topics.
        """
        
        prompt = f"""
You are a curriculum designer. Expand this weekly theme into 7 daily topics.

Week {week_num}: {week_theme}

For each day, provide:
1. Micro-topic (1-2 sentences)
2. Learning objectives (3-5 bullet points)
3. Estimated difficulty (1-5)

Output JSON array:
[
  {{
    "day": 1,
    "micro_topic": "...",
    "objectives": ["...", "..."],
    "difficulty": 3
  }},
  ...
]
"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        days_data = json.loads(response.content[0].text)
        
        days = []
        for d in days_data:
            day = PlanDay(
                day_number=d['day'],
                micro_topic=d['micro_topic'],
                learning_objectives=d['objectives'],
                estimated_hours=3.0,
                difficulty=d['difficulty']
            )
            days.append(day)
        
        return days
    
    def _wrap_json_plan(self, raw_plan: dict) -> LearningPlan:
        """Helper: wrap pre-structured JSON into LearningPlan."""
        # Direct mapping from dict to dataclass
        # ... implementation
        pass


# USAGE EXAMPLES:

# Example 1: Ultra-detailed Markdown (like the 52-week QM plan)
processor = PlanFormatProcessor(anthropic_key="...")
with open('daily_3hr_plan.md', 'r') as f:
    plan_text = f.read()

plan = processor.process_plan(plan_text, format_hint="ultra_detailed")
print(f"Processed {plan.total_weeks} weeks, {len(plan.weeks[0].days)} days/week")

# Example 2: High-level topics
high_level_text = """
Week 1: Introduction to Philosophy
Week 2: Ancient Greek Philosophy
Week 3: Medieval Philosophy
Week 4: Modern Philosophy
"""

plan = processor.process_plan(high_level_text, format_hint="high_level")
# AI expands each week into 7 detailed days

# Example 3: Natural language
natural_text = "I want to learn philosophy, 3 hours per day for 6 months"

plan = processor.process_plan(natural_text, format_hint="natural")
# Full plan generated by AI

# Example 4: Auto-detect
plan = processor.process_plan(some_text, format_hint="auto")
# Automatically detects format and processes
