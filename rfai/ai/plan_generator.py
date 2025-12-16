"""
Plan Generator AI - Generates 52-week learning plans
Can use Anthropic Claude API or fall back to template-based generation
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PlanGeneratorAI:
    """
    Generates comprehensive learning plans from topics
    Uses Claude API if available, otherwise template-based
    """
    
    def __init__(self, anthropic_key: Optional[str] = None):
        """
        Initialize plan generator
        
        Args:
            anthropic_key: Optional Anthropic API key for Claude
        """
        self.anthropic_key = anthropic_key or os.environ.get('ANTHROPIC_API_KEY')
        self.has_anthropic = self.anthropic_key is not None
        
        if self.has_anthropic:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.anthropic_key)
                logger.info("Anthropic API initialized")
            except ImportError:
                logger.warning("anthropic package not installed, using template-based generation")
                self.has_anthropic = False
        else:
            logger.info("No Anthropic API key, using template-based generation")
    
    def generate_plan(
        self,
        topic: str,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a complete learning plan
        
        Args:
            topic: The subject to learn (e.g., "philosophy", "rust programming")
            user_context: Dict with time_available, timeline, learning_style, etc.
        
        Returns:
            Dict with complete plan structure
        """
        if user_context is None:
            user_context = {}
        
        # Default context
        context = {
            "time_available": user_context.get("time_available", "3 hours/day"),
            "timeline": user_context.get("timeline", "6 months"),
            "learning_style": user_context.get("learning_style", "balanced"),
            "current_knowledge": user_context.get("current_knowledge", "beginner")
        }
        
        logger.info(f"Generating plan for topic: {topic}")
        logger.info(f"Context: {context}")
        
        if self.has_anthropic:
            return self._generate_with_claude(topic, context)
        else:
            return self._generate_template_based(topic, context)
    
    def _generate_with_claude(self, topic: str, context: Dict) -> Dict:
        """Generate plan using Claude API"""
        prompt = self._build_claude_prompt(topic, context)
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=15000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            plan_json = json.loads(response.content[0].text)
            logger.info(f"Generated plan with {len(plan_json.get('weeks', []))} weeks")
            return plan_json
            
        except Exception as e:
            logger.error(f"Error generating with Claude: {e}")
            logger.info("Falling back to template-based generation")
            return self._generate_template_based(topic, context)
    
    def _build_claude_prompt(self, topic: str, context: Dict) -> str:
        """Build prompt for Claude"""
        return f"""You are an expert curriculum designer. Generate a personalized learning plan.

TOPIC: {topic}
USER CONTEXT:
- Available time: {context['time_available']}
- Timeline: {context['timeline']}
- Learning style: {context['learning_style']}
- Current knowledge: {context['current_knowledge']}

OUTPUT FORMAT (strict JSON):
{{
  "plan_id": "uuid",
  "topic": "{topic}",
  "estimated_duration_weeks": 26,
  "daily_time_hours": 3,
  "weeks": [
    {{
      "week_number": 1,
      "theme": "Foundations of {topic}",
      "days": [
        {{
          "day_number": 1,
          "date_relative": "Week 1, Monday",
          "micro_topic": "Introduction to {topic}",
          "learning_objectives": ["obj1", "obj2"],
          "time_breakdown": {{
            "00:00-00:45": "Watch intro video",
            "00:45-01:45": "Read chapter 1",
            "01:45-02:30": "Practice problems",
            "02:30-03:00": "Mini-quiz"
          }},
          "resources": [
            {{
              "type": "video",
              "title": "...",
              "url": "...",
              "duration_minutes": 45,
              "difficulty": "beginner"
            }}
          ],
          "mini_quiz": [
            {{"question": "...", "answer": "...", "difficulty": "easy"}}
          ],
          "prerequisites": [],
          "estimated_difficulty": 3
        }}
      ],
      "weekly_quiz": [...],
      "capstone_project": "Build something practical"
    }}
  ],
  "milestones": [
    {{"week": 4, "achievement": "Complete foundations"}},
    {{"week": 12, "achievement": "Intermediate proficiency"}}
  ]
}}

REQUIREMENTS:
1. Each day must have exactly 3 hours of structured activities
2. Include mini-quizzes every day (3-5 questions)
3. Weekly comprehensive quizzes on Sundays (day 7)
4. Mix content types (videos, papers, tutorials, practice)
5. Build logical prerequisite chains
6. Include difficulty estimates
7. Generate at least 4 weeks, up to 26 weeks

Generate the complete plan now as valid JSON.
"""
    
    def _generate_template_based(self, topic: str, context: Dict) -> Dict:
        """Generate plan using templates (fallback when no API)"""
        plan_id = str(uuid.uuid4())
        
        # Estimate duration from context
        timeline = context.get("timeline", "6 months")
        if "month" in timeline:
            weeks = int(timeline.split()[0]) * 4
        else:
            weeks = 26  # Default 6 months
        
        weeks = min(weeks, 52)  # Max 52 weeks
        
        logger.info(f"Generating template-based plan with {weeks} weeks")
        
        # Create base structure
        plan = {
            "plan_id": plan_id,
            "topic": topic,
            "estimated_duration_weeks": weeks,
            "daily_time_hours": 3.0,
            "current_week": 1,
            "current_day": 1,
            "status": "active",
            "weeks": [],
            "milestones": []
        }
        
        # Generate weeks
        for week_num in range(1, min(weeks + 1, 5)):  # Generate first 4 weeks initially
            week = self._generate_week_template(week_num, topic, context)
            plan["weeks"].append(week)
        
        # Add milestones
        plan["milestones"] = [
            {"week": 4, "achievement": f"Foundation of {topic} complete"},
            {"week": 12, "achievement": f"Intermediate {topic} proficiency"},
            {"week": 26, "achievement": f"Advanced {topic} mastery"}
        ]
        
        logger.info(f"Generated template plan: {len(plan['weeks'])} weeks")
        return plan
    
    def _generate_week_template(self, week_num: int, topic: str, context: Dict) -> Dict:
        """Generate a week template"""
        
        # Define phases
        if week_num == 1:
            theme = f"Introduction to {topic}"
            difficulty_base = 1
        elif week_num <= 4:
            theme = f"Foundations of {topic}"
            difficulty_base = 2
        elif week_num <= 12:
            theme = f"Core Concepts in {topic}"
            difficulty_base = 3
        elif week_num <= 26:
            theme = f"Advanced {topic}"
            difficulty_base = 4
        else:
            theme = f"Mastery and Practice - {topic}"
            difficulty_base = 5
        
        week = {
            "week_number": week_num,
            "theme": theme,
            "days": [],
            "weekly_quiz": self._generate_quiz_template(week_num, topic, difficulty_base),
            "capstone_project": f"Week {week_num} Project: Apply {theme}"
        }
        
        # Generate 7 days
        for day_num in range(1, 8):
            if day_num == 7:
                # Sunday - review day
                day = self._generate_review_day(week_num, day_num, topic)
            else:
                day = self._generate_learning_day(week_num, day_num, topic, difficulty_base)
            
            week["days"].append(day)
        
        return week
    
    def _generate_learning_day(self, week_num: int, day_num: int, topic: str, difficulty: int) -> Dict:
        """Generate a learning day template"""
        day_id = str(uuid.uuid4())
        
        return {
            "id": day_id,
            "day_number": day_num,
            "date_relative": f"Week {week_num}, Day {day_num}",
            "micro_topic": f"{topic} - Concept {day_num}",
            "learning_objectives": [
                f"Understand core concept {day_num}",
                f"Apply {topic} principles",
                f"Practice with examples"
            ],
            "time_breakdown": {
                "00:00-00:45": f"Video lecture on {topic}",
                "00:45-01:45": f"Reading: {topic} fundamentals",
                "01:45-02:30": f"Practice exercises",
                "02:30-03:00": "Mini-quiz and review"
            },
            "resources": [
                {
                    "type": "video",
                    "title": f"Introduction to {topic} Concept {day_num}",
                    "url": "",  # To be filled by discovery
                    "duration_minutes": 45,
                    "difficulty": self._difficulty_label(difficulty)
                },
                {
                    "type": "article",
                    "title": f"{topic} Fundamentals - Part {day_num}",
                    "url": "",
                    "duration_minutes": 60,
                    "difficulty": self._difficulty_label(difficulty)
                }
            ],
            "mini_quiz": self._generate_quiz_template(week_num, topic, difficulty, mini=True),
            "prerequisites": [] if day_num == 1 else [f"Week {week_num}, Day {day_num - 1}"],
            "estimated_difficulty": difficulty,
            "completed": False
        }
    
    def _generate_review_day(self, week_num: int, day_num: int, topic: str) -> Dict:
        """Generate a review/quiz day (Sunday)"""
        day_id = str(uuid.uuid4())
        
        return {
            "id": day_id,
            "day_number": day_num,
            "date_relative": f"Week {week_num}, Day {day_num} (Review)",
            "micro_topic": f"Week {week_num} Comprehensive Review",
            "learning_objectives": [
                f"Review all Week {week_num} concepts",
                "Take comprehensive quiz",
                "Identify knowledge gaps"
            ],
            "time_breakdown": {
                "00:00-01:00": "Review notes and materials",
                "01:00-02:15": "Comprehensive quiz",
                "02:15-03:00": "Reflection and planning"
            },
            "resources": [],
            "mini_quiz": [],  # Uses weekly_quiz instead
            "prerequisites": [f"Week {week_num}, Day {i}" for i in range(1, 7)],
            "estimated_difficulty": 3,
            "completed": False
        }
    
    def _generate_quiz_template(self, week_num: int, topic: str, difficulty: int, mini: bool = False) -> List[Dict]:
        """Generate quiz questions template"""
        num_questions = 3 if mini else 10
        
        questions = []
        for i in range(1, num_questions + 1):
            questions.append({
                "question": f"Question {i}: Test your understanding of {topic}",
                "answer": "To be determined based on actual content",
                "difficulty": self._difficulty_label(difficulty),
                "points": 1
            })
        
        return questions
    
    def _difficulty_label(self, level: int) -> str:
        """Convert numeric difficulty to label"""
        if level <= 2:
            return "beginner"
        elif level <= 3:
            return "intermediate"
        else:
            return "advanced"


if __name__ == "__main__":
    # Test the generator
    logging.basicConfig(level=logging.INFO)
    
    generator = PlanGeneratorAI()
    plan = generator.generate_plan(
        "philosophy",
        {"time_available": "3 hours/day", "timeline": "6 months"}
    )
    
    print(json.dumps(plan, indent=2))
