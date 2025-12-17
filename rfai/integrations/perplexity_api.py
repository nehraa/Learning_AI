"""
Perplexity API Integration
Web search and content discovery using Perplexity AI
"""

import os
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class PerplexitySearch:
    """
    Perplexity AI search integration
    Uses Perplexity API for web search and content discovery
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Perplexity search
        
        Args:
            api_key: Perplexity API key
        """
        self.api_key = api_key or os.environ.get('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        
        if not self.api_key:
            logger.warning("No Perplexity API key - using fallback mode")
        else:
            logger.info("Perplexity API initialized")
    
    def search(self, query: str, search_recency_filter: str = "month",
               return_citations: bool = True) -> Dict:
        """
        Search using Perplexity API
        
        Args:
            query: Search query
            search_recency_filter: "day", "week", "month", "year"
            return_citations: Whether to return source citations
        
        Returns:
            Dict with answer and sources
        """
        if not self.api_key:
            logger.error("Perplexity API key not configured")
            return {'answer': '', 'citations': []}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a helpful research assistant. Provide detailed, accurate information with citations.'
                    },
                    {
                        'role': 'user',
                        'content': query
                    }
                ],
                'search_recency_filter': search_recency_filter,
                'return_citations': return_citations
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract answer and citations
            choices = data.get('choices', [])
            if not choices:
                return {'answer': '', 'citations': []}
            
            message = choices[0].get('message', {})
            answer = message.get('content', '')
            citations = data.get('citations', [])
            
            logger.info(f"Perplexity search completed: {len(answer)} chars, {len(citations)} citations")
            
            return {
                'answer': answer,
                'citations': citations,
                'query': query
            }
        
        except Exception as e:
            logger.error(f"Perplexity search error: {e}")
            return {'answer': '', 'citations': []}
    
    def find_resources(self, topic: str, resource_type: str = "tutorial") -> List[Dict]:
        """
        Find learning resources for a topic
        
        Args:
            topic: Learning topic
            resource_type: "tutorial", "article", "documentation", "course"
        
        Returns:
            List of resource dicts
        """
        query = f"Best {resource_type}s for learning {topic} in 2025. Include URLs and brief descriptions."
        
        result = self.search(query, search_recency_filter="month")
        
        if not result.get('answer'):
            return []
        
        # Parse resources from answer and citations
        resources = []
        
        # Extract from citations
        for i, citation in enumerate(result.get('citations', [])[:10]):
            resources.append({
                'id': f'perplexity_{i}',
                'type': resource_type,
                'source': 'perplexity',
                'title': citation.split('//')[-1].split('/')[0],  # Extract domain
                'url': citation,
                'description': f'Resource for {topic}',
                'relevance_score': 0.9 - (i * 0.05)  # Decrease by position
            })
        
        logger.info(f"Found {len(resources)} resources for {topic}")
        return resources
    
    def get_topic_overview(self, topic: str) -> str:
        """
        Get a comprehensive overview of a topic
        
        Args:
            topic: Topic to research
        
        Returns:
            Overview text
        """
        query = f"""Provide a comprehensive overview of {topic}:
1. What it is and why it's important
2. Key concepts and prerequisites
3. Learning path recommendations
4. Best resources for beginners
5. Common challenges and how to overcome them"""
        
        result = self.search(query, search_recency_filter="month")
        return result.get('answer', '')
    
    def find_recent_developments(self, topic: str, days: int = 30) -> List[Dict]:
        """
        Find recent developments in a topic
        
        Args:
            topic: Topic to research
            days: How many days back to search
        
        Returns:
            List of recent developments
        """
        recency = "day" if days <= 1 else "week" if days <= 7 else "month"
        query = f"Latest developments and news about {topic} in the last {days} days"
        
        result = self.search(query, search_recency_filter=recency)
        
        developments = []
        for i, citation in enumerate(result.get('citations', [])[:5]):
            developments.append({
                'id': f'dev_{i}',
                'source': citation,
                'summary': f'Recent development in {topic}',
                'date': 'recent'
            })
        
        return developments
    
    def compare_resources(self, resource1: str, resource2: str, topic: str) -> str:
        """
        Compare two learning resources
        
        Args:
            resource1: First resource name
            resource2: Second resource name  
            topic: Topic context
        
        Returns:
            Comparison text
        """
        query = f"Compare {resource1} vs {resource2} for learning {topic}. Which is better and why?"
        
        result = self.search(query)
        return result.get('answer', '')
    
    def suggest_learning_path(self, topic: str, current_level: str = "beginner",
                             time_available: str = "3 hours/day") -> str:
        """
        Get AI-suggested learning path
        
        Args:
            topic: Topic to learn
            current_level: "beginner", "intermediate", "advanced"
            time_available: Time commitment
        
        Returns:
            Learning path recommendations
        """
        query = f"""Create a detailed learning path for {topic}:
- Current level: {current_level}
- Time available: {time_available}
- Include specific resources, order, and estimated time
- Focus on practical, hands-on learning"""
        
        result = self.search(query, search_recency_filter="month")
        return result.get('answer', '')


if __name__ == "__main__":
    # Test Perplexity API
    logging.basicConfig(level=logging.INFO)
    
    perplexity = PerplexitySearch()
    
    if perplexity.api_key:
        print("✅ Perplexity API configured")
        
        # Test search
        result = perplexity.search("What is reinforcement learning?")
        print(f"\nSearch result: {len(result.get('answer', ''))} chars")
        print(f"Citations: {len(result.get('citations', []))}")
        
        # Test resource finding
        resources = perplexity.find_resources("machine learning", "tutorial")
        print(f"\nFound {len(resources)} resources")
    else:
        print("❌ Perplexity API key not configured")
        print("Set PERPLEXITY_API_KEY environment variable")
        print("Get key from: https://www.perplexity.ai/settings/api")
