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
            List of movie dicts with title, director, year, imdb_rating, poster_url
        """
        if not self.imdb_client or not self.imdb_client.api_key:
            logger.warning("IMDB client not configured - using artistic film search")
            return self._fetch_movies_via_artistic_search()
        
        try:
            directors = self.config.get('movie_interests', {}).get('directors', [])
            genres = self.config.get('movie_interests', {}).get('genres', [])
            
            movies = []
            seen_ids = set()
            
            # Search by each director
            for director in directors[:3]:  # Top 3 directors
                try:
                    results = self.imdb_client.search_by_director(
                        director=director,
                        min_rating=7.0,
                        max_results=max_results // 2
                    )
                    for m in results:
                        if m.get('imdb_id') not in seen_ids:
                            seen_ids.add(m.get('imdb_id'))
                            movies.append(self._normalize_movie(m))
                except Exception as e:
                    logger.warning(f"Error searching director {director}: {e}")
                    continue
            
            if not movies:
                logger.warning("Director search returned no results, trying artistic films")
                return self._fetch_movies_via_artistic_search()
            
            return movies[:max_results]
        except Exception as e:
            logger.error(f"Error fetching movies: {e}")
            return self._fetch_movies_via_artistic_search()
    
    def _fetch_movies_via_artistic_search(self) -> List[Dict]:
        """
        Fallback: Fetch movies using artistic film search
        """
        try:
            if not self.imdb_client or not self.imdb_client.api_key:
                return self._get_sample_movies()
            
            movies = self.imdb_client.search_artistic_films(max_results=10, min_rating=7.0)
            return [self._normalize_movie(m) for m in movies]
        except Exception as e:
            logger.error(f"Artistic search failed: {e}")
            return self._get_sample_movies_curated()
    
    def _normalize_movie(self, movie: Dict) -> Dict:
        """
        Normalize movie data to ensure all required fields exist
        
        Args:
            movie: Raw movie dict from IMDB API
        
        Returns:
            Normalized movie dict with all required fields
        """
        # Get poster with fallback
        poster_url = movie.get('poster_url') or movie.get('poster')
        
        # Validate poster URL - OMDb sometimes returns "N/A" or invalid URLs
        if not poster_url or poster_url == 'N/A' or not poster_url.startswith('http'):
            # Generate fallback poster from IMDb
            imdb_id = movie.get('imdb_id')
            if imdb_id:
                poster_url = f'https://www.imdb.com/title/{imdb_id}/mediaindex'
            else:
                poster_url = None
        
        return {
            'id': movie.get('id') or movie.get('imdb_id') or 'unknown',
            'title': movie.get('title') or 'Unknown Title',
            'director': movie.get('director') or 'Unknown Director',
            'year': movie.get('year') or 0,
            'rating': movie.get('imdb_rating') or 0.0,
            'runtime': movie.get('runtime') or 'N/A',
            'genres': movie.get('genre') or [],
            'plot': movie.get('plot') or '',
            'poster': poster_url,  # Use 'poster' key for dashboard compatibility
            'poster_url': poster_url,
            'url': f'https://www.imdb.com/title/{movie.get("imdb_id")}/' if movie.get('imdb_id') else '#',
            'imdb_id': movie.get('imdb_id'),
            'source': 'imdb'
        }

    
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
    
    def _get_sample_movies_curated(self) -> List[Dict]:
        """Curated sample movies - highly rated artistic films"""
        return [
            {
                'id': 'tt0068646',
                'title': 'The Godfather',
                'director': 'Francis Ford Coppola',
                'year': 1972,
                'rating': 9.2,
                'genres': ['Crime', 'Drama'],
                'runtime': '175 min',
                'plot': 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant youngest son.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTMyLWFwM2ItYTIxMWFiZjQ4YjI1XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt0068646/',
                'source': 'sample'
            },
            {
                'id': 'tt0110912',
                'title': 'Pulp Fiction',
                'director': 'Quentin Tarantino',
                'year': 1994,
                'rating': 8.9,
                'genres': ['Crime', 'Drama'],
                'runtime': '154 min',
                'plot': 'The lives of two mob hitmen, a boxer, a gangster\'s wife, and a pair of diner bandits intertwine in four tales of violence and redemption.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItMDJlM2RlMzA5NTA1XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt0110912/',
                'source': 'sample'
            },
            {
                'id': 'tt0816692',
                'title': 'Inception',
                'director': 'Christopher Nolan',
                'year': 2010,
                'rating': 8.8,
                'genres': ['Action', 'Sci-Fi', 'Thriller'],
                'runtime': '148 min',
                'plot': 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt0816692/',
                'source': 'sample'
            },
            {
                'id': 'tt0111161',
                'title': 'The Shawshank Redemption',
                'director': 'Frank Darabont',
                'year': 1994,
                'rating': 9.3,
                'genres': ['Drama'],
                'runtime': '142 min',
                'plot': 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BMDFlYTAwYjktMDJjMC00MjgyLWJmNDctNTI5OTQ0YzZjMDk1XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt0111161/',
                'source': 'sample'
            },
            {
                'id': 'tt0133093',
                'title': 'The Matrix',
                'director': 'Lana Wachowski, Lilly Wachowski',
                'year': 1999,
                'rating': 8.7,
                'genres': ['Action', 'Sci-Fi'],
                'runtime': '136 min',
                'plot': 'A computer programmer discovers that reality as he knows it is a simulation created by machines.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDl2ODA4NjU2NjE4XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt0133093/',
                'source': 'sample'
            },
            {
                'id': 'tt0468569',
                'title': 'The Dark Knight',
                'director': 'Christopher Nolan',
                'year': 2008,
                'rating': 9.0,
                'genres': ['Action', 'Crime', 'Drama'],
                'runtime': '152 min',
                'plot': 'When the menace known as the Joker wreaks havoc and chaos on Gotham, Batman must accept one of the greatest psychological challenges.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BMTk4ODQzNDY3Ml5BMl5BanBnXkFtZTcwODA0NTM4Nw@@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt0468569/',
                'source': 'sample'
            },
            {
                'id': 'tt1345836',
                'title': 'The Dark Knight Rises',
                'director': 'Christopher Nolan',
                'year': 2012,
                'rating': 8.4,
                'genres': ['Action', 'Adventure', 'Crime'],
                'runtime': '164 min',
                'plot': 'Eight years after the Joker\'s reign of anarchy, Batman must face a new threat that brings Gotham to the brink of destruction.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BNjc1RjU0YzEtMjE2MC00ZDZlLTljN2QtNzAxNTI5MDA1MzA1XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt1345836/',
                'source': 'sample'
            },
            {
                'id': 'tt0482571',
                'title': 'The Prestige',
                'director': 'Christopher Nolan',
                'year': 2006,
                'rating': 8.5,
                'genres': ['Drama', 'Mystery', 'Sci-Fi'],
                'runtime': '130 min',
                'plot': 'After a tragic accident, two stage magicians engage in battle to create the ultimate illusion while sacrificing everything to outwit each other.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BMTU1MzAwMjA5MF5BMl5BanBnXkFtZTcwMDU3NDk1Mw@@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt0482571/',
                'source': 'sample'
            },
            {
                'id': 'tt0816692',
                'title': 'Interstellar',
                'director': 'Christopher Nolan',
                'year': 2014,
                'rating': 8.6,
                'genres': ['Adventure', 'Drama', 'Sci-Fi'],
                'runtime': '169 min',
                'plot': 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDctMzg5Ni00NGE4LWJmNDQtZjA4MDI3NzYzODMyXkEyXkFqcGdeQXVyMzQ0MjM5NzM@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt0816692/',
                'source': 'sample'
            },
            {
                'id': 'tt1375666',
                'title': 'Tenet',
                'director': 'Christopher Nolan',
                'year': 2020,
                'rating': 7.4,
                'genres': ['Action', 'Sci-Fi', 'Thriller'],
                'runtime': '150 min',
                'plot': 'Armed with only one word, Tenet, and fighting for the survival of the entire world, a Protagonist journeys through a twilight world of international espionage.',
                'poster': 'https://m.media-amazon.com/images/M/MV5BMDZkYmVkNDctY2NlNS00NTk0LWFlMDAtYzAxZDQyZGEwZWZhXkEyXkFqcGdeQXVyMzg0MjcwOTg@._V1_SX300.jpg',
                'url': 'https://www.imdb.com/title/tt1375666/',
                'source': 'sample'
            }
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
