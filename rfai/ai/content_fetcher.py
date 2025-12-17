"""
Content Fetcher - Fetches real content from integrations
Uses YouTube, ArXiv, IMDB, Perplexity APIs to get actual recommendations
"""

import logging
import os
from typing import List, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ContentFetcher:
    """
    Fetches actual content from various sources based on learning topics
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize content fetcher with API integrations"""
        if config_path is None:
            config_path = Path.cwd() / "interests.json"
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize API clients
        self.youtube_client = None
        self.arxiv_client = None
        self.perplexity_client = None
        self.imdb_client = None
        
        self._init_clients()
    
    def _load_config(self) -> Dict:
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _init_clients(self):
        """Initialize API clients"""
        try:
            from rfai.integrations.youtube_api import YouTubeDiscovery
            self.youtube_client = YouTubeDiscovery()
            logger.info("YouTube client initialized")
        except Exception as e:
            logger.warning(f"YouTube client failed: {e}")
        
        try:
            from rfai.integrations.arxiv_api import ArXivDiscovery
            self.arxiv_client = ArXivDiscovery()
            logger.info("ArXiv client initialized")
        except Exception as e:
            logger.warning(f"ArXiv client failed: {e}")
        
        try:
            from rfai.integrations.perplexity_api import PerplexitySearch
            self.perplexity_client = PerplexitySearch()
            logger.info("Perplexity client initialized")
        except Exception as e:
            logger.warning(f"Perplexity client failed: {e}")
        
        try:
            from rfai.integrations.imdb_api import IMDbDiscovery
            self.imdb_client = IMDbDiscovery()
            logger.info("IMDB client initialized")
        except Exception as e:
            logger.warning(f"IMDB client failed: {e}")
    
    def fetch_science_youtube(self, max_results: int = 10) -> List[Dict]:
        """
        Fetch actual science YouTube videos
        
        Returns:
            List of video dicts with title, url, channel, duration, etc.
        """
        if not self.youtube_client or not self.youtube_client.api_key:
            logger.warning("YouTube API not configured - returning sample data")
            return self._get_sample_youtube_science()
        
        try:
            topics = self.config.get('youtube_interests', {}).get('science_topics', [])
            videos = []
            
            for topic in topics[:3]:  # Search top 3 topics
                query = f"{topic} educational"
                results = self.youtube_client.search_videos(
                    query=query,
                    max_results=max_results // 3,
                    duration='medium',
                    order='relevance'
                )
                videos.extend(results)
            
            return videos[:max_results]
        except Exception as e:
            logger.error(f"Error fetching YouTube videos: {e}")
            return self._get_sample_youtube_science()
    
    def fetch_self_help_youtube(self, max_results: int = 10) -> List[Dict]:
        """Fetch self-help YouTube videos"""
        if not self.youtube_client or not self.youtube_client.api_key:
            return self._get_sample_youtube_selfhelp()
        
        try:
            topics = self.config.get('youtube_interests', {}).get('self_help_topics', [])
            videos = []
            
            for topic in topics[:3]:
                query = f"{topic} book summary"
                results = self.youtube_client.search_videos(
                    query=query,
                    max_results=max_results // 3,
                    duration='short',
                    order='relevance'
                )
                videos.extend(results)
            
            return videos[:max_results]
        except Exception as e:
            logger.error(f"Error fetching self-help videos: {e}")
            return self._get_sample_youtube_selfhelp()
    
    def fetch_research_papers(self, max_results: int = 10) -> List[Dict]:
        """
        Fetch research papers from ArXiv
        
        Returns:
            List of paper dicts with title, abstract, authors, url
        """
        if not self.arxiv_client:
            return self._get_sample_papers()
        
        try:
            topics = self.config.get('research_interests', {}).get('topics', [])
            categories = self.config.get('research_interests', {}).get('arxiv_categories', [])
            
            papers = []
            for topic in topics[:2]:
                results = self.arxiv_client.search_papers(
                    query=topic,
                    max_results=max_results // 2,
                    categories=categories,
                    sort_by='relevance'
                )
                papers.extend(results)
            
            return papers[:max_results]
        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return self._get_sample_papers()
    
    def fetch_movies(self, max_results: int = 10) -> List[Dict]:
        """
        Fetch movie recommendations
        
        Returns:
            List of movie dicts with title, director, year, imdb_rating
        """
        if not self.imdb_client:
            return self._get_sample_movies()
        
        try:
            directors = self.config.get('movie_interests', {}).get('directors', [])
            genres = self.config.get('movie_interests', {}).get('genres', [])
            
            movies = []
            for director in directors[:3]:
                results = self.imdb_client.search_by_director(
                    director=director,
                    min_rating=7.0,
                    max_results=max_results // 3
                )
                movies.extend(results)
            
            return movies[:max_results]
        except Exception as e:
            logger.error(f"Error fetching movies: {e}")
            return self._get_sample_movies()
    
    def get_study_plan_content(self, study_plan: str) -> Dict:
        """
        Use Perplexity to fetch content based on study plan
        
        Args:
            study_plan: User's study plan text
        
        Returns:
            Dict with recommended content across all types
        """
        if not self.perplexity_client or not self.perplexity_client.api_key:
            logger.warning("Perplexity API not configured")
            return self._generate_study_content_fallback(study_plan)
        
        try:
            # Ask Perplexity for content recommendations
            query = f"""Based on this study plan:
{study_plan}

Please provide:
1. Top 5 YouTube channels or videos to watch
2. Top 5 research papers or articles to read
3. Top 3 books to study
4. Key topics to focus on

Format the response with clear sections."""
            
            result = self.perplexity_client.search(
                query=query,
                search_recency_filter="month",
                return_citations=True
            )
            
            return {
                'recommendations': result.get('answer', ''),
                'sources': result.get('citations', []),
                'generated_at': 'perplexity',
                'study_plan': study_plan
            }
        except Exception as e:
            logger.error(f"Error getting Perplexity recommendations: {e}")
            return self._generate_study_content_fallback(study_plan)
    
    # Sample data fallbacks (when APIs not configured)
    
    def _get_sample_youtube_science(self) -> List[Dict]:
        """Sample science videos"""
        topics = self.config.get('youtube_interests', {}).get('science_topics', [])
        return [
            {
                'id': f'sample_{i}',
                'title': f'{topic} - Educational Overview',
                'channel': 'Sample Channel',
                'url': f'https://youtube.com/watch?v=sample{i}',
                'duration': '15:30',
                'views': 100000,
                'thumbnail': f'https://i.ytimg.com/vi/sample{i}/default.jpg',
                'description': f'Learn about {topic} in this comprehensive video',
                'published': '2024-12-01'
            }
            for i, topic in enumerate(topics[:5])
        ]
    
    def _get_sample_youtube_selfhelp(self) -> List[Dict]:
        """Sample self-help videos"""
        topics = self.config.get('youtube_interests', {}).get('self_help_topics', [])
        return [
            {
                'id': f'selfhelp_{i}',
                'title': f'{topic} - Key Lessons',
                'channel': 'Self-Help Channel',
                'url': f'https://youtube.com/watch?v=selfhelp{i}',
                'duration': '8:45',
                'views': 50000,
                'thumbnail': f'https://i.ytimg.com/vi/selfhelp{i}/default.jpg',
                'description': f'Practical advice on {topic}',
                'published': '2024-12-10'
            }
            for i, topic in enumerate(topics[:5])
        ]
    
    def _get_sample_papers(self) -> List[Dict]:
        """Sample research papers"""
        topics = self.config.get('research_interests', {}).get('topics', [])
        return [
            {
                'id': f'arxiv.{2024}.{1000+i}',
                'title': f'Recent Advances in {topic}',
                'authors': ['Author A', 'Author B'],
                'abstract': f'This paper discusses recent developments in {topic}...',
                'url': f'https://arxiv.org/abs/2024.{1000+i}',
                'published': '2024-12-01',
                'categories': ['cs.AI', 'quant-ph']
            }
            for i, topic in enumerate(topics[:5])
        ]
    
    def _get_sample_movies(self) -> List[Dict]:
        """Sample movies"""
        directors = self.config.get('movie_interests', {}).get('directors', [])
        return [
            {
                'id': f'tt000000{i}',
                'title': f'Great Film by {director}',
                'director': director,
                'year': 2020 - i,
                'rating': 8.0 + (i * 0.1),
                'genres': ['Drama', 'Art'],
                'runtime': '120 min',
                'url': f'https://www.imdb.com/title/tt000000{i}/',
                'poster': f'https://m.media-amazon.com/images/sample{i}.jpg'
            }
            for i, director in enumerate(directors[:5])
        ]
    
    def _generate_study_content_fallback(self, study_plan: str) -> Dict:
        """Fallback content generation without Perplexity"""
        return {
            'recommendations': f"""Based on your study plan, here are recommendations:

1. YouTube Videos:
   - Search for educational videos on each topic
   - Look for channels with high production quality
   - Focus on videos with transcripts available

2. Research Papers:
   - Use Google Scholar for each topic
   - Check ArXiv for latest research
   - Read review papers first

3. Books:
   - Find textbooks for each subject
   - Read foundational works
   - Study from multiple sources

4. Practice:
   - Solve problems daily
   - Take practice tests
   - Review mistakes regularly
""",
            'sources': [],
            'generated_at': 'fallback',
            'study_plan': study_plan
        }
