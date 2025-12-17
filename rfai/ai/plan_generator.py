"""
Plan Generator AI - Generates 52-week learning plans
Uses Ollama (local LLM) or Perplexity API, with template fallback
"""

import json
import uuid
from typing import Dict, List, Optional
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class PlanGeneratorAI:
    """
    Generates comprehensive learning plans from topics
    Priority: Ollama (local) > Perplexity > Template-based
    """
    
    def __init__(self, ollama_model: Optional[str] = None, 
                 perplexity_key: Optional[str] = None):
        """
        Initialize plan generator
        
        Args:
            ollama_model: Ollama model name (e.g., 'llama3.2:3b')
            perplexity_key: Perplexity API key (fallback if Ollama unavailable)
        """
        self.ai_client = None
        self.ai_mode = 'template'  # Default to template
        
        # Try Ollama first (local, preferred)
        try:
            from rfai.integrations.ollama_client import OllamaClient
            ollama = OllamaClient(model=ollama_model)
            if ollama.available:
                self.ai_client = ollama
                self.ai_mode = 'ollama'
                logger.info("Using Ollama for plan generation (local)")
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
        
        # Try Perplexity as fallback
        if not self.ai_client:
            try:
                from rfai.integrations.perplexity_api import PerplexitySearch
                perplexity = PerplexitySearch(api_key=perplexity_key)
                if perplexity.api_key:
                    self.ai_client = perplexity
                    self.ai_mode = 'perplexity'
                    logger.info("Using Perplexity for plan generation")
            except Exception as e:
                logger.debug(f"Perplexity not available: {e}")
        
        # Fallback to template
        if not self.ai_client:
            logger.info("No AI available, using template-based generation")
    
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
        logger.info(f"AI mode: {self.ai_mode}")
        
        if self.ai_mode == 'ollama':
            return self._generate_with_ollama(topic, context)
        elif self.ai_mode == 'perplexity':
            return self._generate_with_perplexity(topic, context)
        else:
            return self._generate_template_based(topic, context)
    
    def _generate_with_ollama(self, topic: str, context: Dict) -> Dict:
        """Generate plan using Ollama (local LLM)"""
        try:
            plan = self.ai_client.generate_plan(topic, context)
            logger.info(f"Generated plan with {len(plan.get('weeks', []))} weeks using Ollama")
            return plan
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            logger.info("Falling back to template-based generation")
            return self._generate_template_based(topic, context)
    
    def _generate_with_perplexity(self, topic: str, context: Dict) -> Dict:
        """Generate plan using Perplexity API"""
        try:
            # Use Perplexity to get learning path
            learning_path = self.ai_client.suggest_learning_path(
                topic,
                current_level=context.get('current_knowledge', 'beginner'),
                time_available=context.get('time_available', '3 hours/day')
            )
            
            # Parse into structured plan
            # For now, use template and enhance with Perplexity insights
            plan = self._generate_template_based(topic, context)
            
            # Add AI insights to first week
            if learning_path and len(plan['weeks']) > 0:
                plan['weeks'][0]['ai_insights'] = learning_path[:500]
            
            logger.info(f"Generated plan with Perplexity insights")
            return plan
        except Exception as e:
            logger.error(f"Error generating with Perplexity: {e}")
            return self._generate_template_based(topic, context)
    
    def _generate_template_based(self, topic: str, context: Dict) -> Dict:
        """Generate plan using templates (fallback when no API)"""
        plan_id = str(uuid.uuid4())
        
        # Dynamic duration estimation based on topic complexity and user
        weeks = self._estimate_duration(topic, context)
        
        logger.info(f"Generating template-based plan with {weeks} weeks for '{topic}'")
        
        # Get daily time commitment
        time_available = context.get("time_available", "3 hours/day")
        daily_hours = float(time_available.split()[0]) if "hour" in time_available else 3.0
        
        # Create base structure
        plan = {
            "plan_id": plan_id,
            "topic": topic,
            "estimated_duration_weeks": weeks,
            "daily_time_hours": daily_hours,
            "current_week": 1,
            "current_day": 1,
            "status": "active",
            "weeks": [],
            "milestones": [],
            "adaptive": True,  # Can be adjusted by RL
            "complexity": self._estimate_complexity(topic)
        }
        
        # Generate initial weeks (4-8 based on total duration)
        initial_weeks = min(8, weeks)
        for week_num in range(1, initial_weeks + 1):
            week = self._generate_week_template(week_num, topic, context)
            plan["weeks"].append(week)
        
        # Add dynamic milestones based on duration
        plan["milestones"] = self._generate_milestones(weeks, topic)
        
        logger.info(f"Generated adaptive plan: {len(plan['weeks'])} initial weeks (total: {weeks})")
        return plan
    
    def _estimate_duration(self, topic: str, context: Dict) -> int:
        """
        Dynamically estimate learning duration based on topic and user context
        Not everything needs 52 weeks - fast learners need less time
        """
        # Check explicit timeline
        timeline = context.get("timeline", "")
        if "week" in timeline:
            return min(int(timeline.split()[0]), 52)
        elif "month" in timeline:
            return min(int(timeline.split()[0]) * 4, 52)
        
        # Estimate based on topic complexity
        topic_lower = topic.lower()
        
        # Quick skills (2-8 weeks)
        quick_topics = ["git", "markdown", "bash", "sql basics", "html", "css"]
        if any(quick in topic_lower for quick in quick_topics):
            return 4  # 1 month
        
        # Medium complexity (8-16 weeks)
        medium_topics = ["python basics", "javascript", "react", "flask", "django basics"]
        if any(medium in topic_lower for medium in medium_topics):
            return 12  # 3 months
        
        # Advanced topics (16-26 weeks)
        advanced_topics = ["machine learning", "algorithms", "system design", "quantum"]
        if any(adv in topic_lower for adv in advanced_topics):
            base_weeks = 20  # 5 months
            # Adjust for learning speed
            current_knowledge = context.get("current_knowledge", "beginner")
            if current_knowledge in ["intermediate", "advanced"]:
                return int(base_weeks * 0.7)  # 14 weeks for experienced
            return base_weeks
        
        # Very advanced (26-40 weeks)
        expert_topics = ["quantum mechanics", "category theory", "advanced mathematics", 
                        "compiler design", "distributed systems"]
        if any(exp in topic_lower for exp in expert_topics):
            base_weeks = 32  # 8 months
            # Adjust for learning speed
            current_knowledge = context.get("current_knowledge", "beginner")
            if current_knowledge in ["intermediate", "advanced"]:
                return int(base_weeks * 0.7)  # 22 weeks for experienced
            return base_weeks
        
        # Default: moderate duration
        current_knowledge = context.get("current_knowledge", "beginner")
        if current_knowledge in ["intermediate", "advanced"]:
            return 8  # Experienced learner, unknown topic
        return 12  # 3 months for average topic
    
    def _estimate_complexity(self, topic: str) -> str:
        """Estimate topic complexity"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ["quantum", "category", "advanced", "theoretical"]):
            return "very_high"
        elif any(word in topic_lower for word in ["machine learning", "algorithms", "cryptography"]):
            return "high"
        elif any(word in topic_lower for word in ["python", "javascript", "react", "database"]):
            return "medium"
        else:
            return "low"
    
    def _generate_milestones(self, total_weeks: int, topic: str) -> List[Dict]:
        """Generate dynamic milestones based on plan duration"""
        milestones = []
        
        # Early milestone (10-20% through)
        early = max(2, total_weeks // 5)
        milestones.append({
            "week": early,
            "achievement": f"Fundamentals of {topic} mastered"
        })
        
        # Mid milestone (40-50%)
        mid = max(early + 2, total_weeks // 2)
        if mid < total_weeks:
            milestones.append({
                "week": mid,
                "achievement": f"Core {topic} concepts applied"
            })
        
        # Late milestone (80-90%)
        late = max(mid + 2, int(total_weeks * 0.85))
        if late < total_weeks:
            milestones.append({
                "week": late,
                "achievement": f"Advanced {topic} proficiency"
            })
        
        return milestones
    
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
