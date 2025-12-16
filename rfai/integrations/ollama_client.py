"""
Ollama Client - Local LLM inference
Replaces Claude/Anthropic API for plan generation and content processing
Uses lightweight models like Llama 3.2 3B or similar 7B models
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for Ollama local LLM inference
    Supports models up to 7B parameters
    """
    
    def __init__(self, base_url: str = None, model: str = None):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name (default: llama3.2:3b or phi3:mini)
        """
        self.base_url = base_url or os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model or os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
        
        logger.info(f"Ollama client initialized: {self.base_url}, model: {self.model}")
        
        # Check if server is available
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.info(f"Ollama available with {len(models)} models")
                return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
        return False
    
    def generate(self, prompt: str, system: str = None, max_tokens: int = 4000, 
                 temperature: float = 0.7, json_mode: bool = False) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Max tokens to generate
            temperature: Sampling temperature (0-1)
            json_mode: Force JSON output
        
        Returns:
            Generated text
        """
        if not self.available:
            raise RuntimeError("Ollama server not available")
        
        # Build request
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        if json_mode:
            payload["format"] = "json"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
        
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 4000,
             temperature: float = 0.7, json_mode: bool = False) -> str:
        """
        Chat completion using Ollama
        
        Args:
            messages: List of {role: "system/user/assistant", content: "..."}
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            json_mode: Force JSON output
        
        Returns:
            Assistant response
        """
        if not self.available:
            raise RuntimeError("Ollama server not available")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '')
        
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise
    
    def generate_plan(self, topic: str, user_context: Dict) -> Dict:
        """
        Generate a learning plan using Ollama
        
        Args:
            topic: Learning topic
            user_context: User preferences (timeline, time_available, etc.)
        
        Returns:
            Plan as dict
        """
        system_prompt = """You are an expert curriculum designer. Generate personalized learning plans in JSON format.
Focus on practical, actionable daily schedules with 3-hour breakdowns."""
        
        user_prompt = f"""Generate a comprehensive learning plan for: {topic}

User Context:
- Time available: {user_context.get('time_available', '3 hours/day')}
- Timeline: {user_context.get('timeline', '6 months')}
- Learning style: {user_context.get('learning_style', 'balanced')}
- Current knowledge: {user_context.get('current_knowledge', 'beginner')}

Generate a JSON plan with this structure:
{{
  "topic": "{topic}",
  "estimated_duration_weeks": 26,
  "daily_time_hours": 3,
  "weeks": [
    {{
      "week_number": 1,
      "theme": "Foundations",
      "days": [
        {{
          "day_number": 1,
          "micro_topic": "Introduction to {topic}",
          "learning_objectives": ["obj1", "obj2", "obj3"],
          "time_breakdown": {{
            "00:00-00:45": "Activity 1",
            "00:45-01:45": "Activity 2",
            "01:45-02:30": "Activity 3",
            "02:30-03:00": "Mini-quiz"
          }},
          "resources": [
            {{"type": "video", "title": "...", "difficulty": "beginner"}}
          ],
          "mini_quiz": [
            {{"question": "...", "answer": "...", "difficulty": "easy"}}
          ]
        }}
      ]
    }}
  ]
}}

Generate at least 4 weeks with 7 days each. Include detailed time breakdowns and quizzes."""
        
        try:
            response = self.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], json_mode=True, max_tokens=8000)
            
            # Parse JSON
            plan = json.loads(response)
            logger.info(f"Generated plan for {topic} with {len(plan.get('weeks', []))} weeks")
            return plan
        
        except Exception as e:
            logger.error(f"Plan generation error: {e}")
            raise
    
    def summarize_content(self, content: str, max_length: int = 500) -> str:
        """
        Summarize content using Ollama
        
        Args:
            content: Text to summarize
            max_length: Max summary length
        
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following content in {max_length} words or less. 
Focus on key concepts and actionable insights.

Content:
{content[:4000]}

Summary:"""
        
        return self.generate(prompt, max_tokens=max_length, temperature=0.3)
    
    def extract_concepts(self, content: str) -> List[str]:
        """
        Extract key concepts from content
        
        Args:
            content: Text to analyze
        
        Returns:
            List of key concepts
        """
        prompt = f"""Extract the top 5-10 key concepts from this content.
Return as a JSON array of strings.

Content:
{content[:4000]}

Key concepts (JSON array):"""
        
        try:
            response = self.generate(prompt, json_mode=True, temperature=0.3)
            concepts = json.loads(response)
            if isinstance(concepts, list):
                return concepts
            return []
        except:
            return []
    
    def generate_flashcards(self, content: str, num_cards: int = 5) -> List[Dict]:
        """
        Generate flashcards from content
        
        Args:
            content: Source content
            num_cards: Number of cards to generate
        
        Returns:
            List of flashcard dicts {front, back, difficulty}
        """
        prompt = f"""Generate {num_cards} flashcards from this content.
Return as JSON array with format: [{{"front": "Q?", "back": "A", "difficulty": "easy/medium/hard"}}]

Content:
{content[:4000]}

Flashcards (JSON):"""
        
        try:
            response = self.generate(prompt, json_mode=True, temperature=0.5)
            cards = json.loads(response)
            if isinstance(cards, list):
                return cards[:num_cards]
            return []
        except:
            return []


if __name__ == "__main__":
    # Test Ollama client
    logging.basicConfig(level=logging.INFO)
    
    client = OllamaClient()
    
    if client.available:
        print("✅ Ollama is available")
        
        # Test generation
        response = client.generate("Explain quantum computing in 50 words.")
        print(f"\nGeneration test:\n{response}")
        
        # Test chat
        response = client.chat([
            {"role": "system", "content": "You are a helpful tutor."},
            {"role": "user", "content": "What is machine learning?"}
        ])
        print(f"\nChat test:\n{response}")
    else:
        print("❌ Ollama not available")
        print("Install: https://ollama.ai")
        print("Run: ollama serve")
        print("Pull model: ollama pull llama3.2:3b")
