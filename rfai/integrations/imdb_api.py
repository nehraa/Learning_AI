"""
IMDB API Integration
Movie and documentary discovery for educational/recreational content
"""

import os
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class IMDBDiscovery:
    """
    IMDB content discovery using OMDb API (Open Movie Database)
    Free API with 1000 requests/day
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize IMDB discovery
        
        Args:
            api_key: OMDb API key (get from http://www.omdbapi.com/apikey.aspx)
        """
        self.api_key = api_key or os.environ.get('OMDB_API_KEY')
        self.base_url = "http://www.omdbapi.com/"
        
        if not self.api_key:
            logger.warning("No OMDb API key - using fallback mode")
        else:
            logger.info("OMDb API initialized")
    
    def search_movies(self, query: str, year: Optional[int] = None,
                     movie_type: str = 'movie') -> List[Dict]:
        """
        Search for movies/documentaries
        
        Args:
            query: Search query
            year: Release year (optional)
            movie_type: 'movie', 'series', 'episode'
        
        Returns:
            List of movie dicts
        """
        if not self.api_key:
            logger.error("OMDb API key not configured")
            return []
        
        try:
            params = {
                'apikey': self.api_key,
                's': query,
                'type': movie_type
            }
            
            if year:
                params['y'] = year
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('Response') != 'True':
                logger.warning(f"OMDb search failed: {data.get('Error')}")
                return []
            
            movies = []
            for item in data.get('Search', []):
                # Get detailed info
                details = self.get_movie_details(item['imdbID'])
                if details:
                    movies.append(details)
            
            logger.info(f"Found {len(movies)} movies for query: {query}")
            return movies
        
        except Exception as e:
            logger.error(f"OMDb search error: {e}")
            return []
    
    def get_movie_details(self, imdb_id: str) -> Optional[Dict]:
        """
        Get detailed information about a movie
        
        Args:
            imdb_id: IMDB ID (e.g., 'tt0111161')
        
        Returns:
            Movie details dict
        """
        if not self.api_key:
            return None
        
        try:
            params = {
                'apikey': self.api_key,
                'i': imdb_id,
                'plot': 'full'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('Response') != 'True':
                return None
            
            # Parse and normalize
            return {
                'id': f'imdb_{imdb_id}',
                'imdb_id': imdb_id,
                'type': 'movie',
                'source': 'imdb',
                'title': data.get('Title'),
                'year': int(data.get('Year', '0')),
                'rated': data.get('Rated'),
                'runtime': data.get('Runtime'),
                'genre': data.get('Genre', '').split(', '),
                'director': data.get('Director'),
                'actors': data.get('Actors', '').split(', '),
                'plot': data.get('Plot'),
                'language': data.get('Language'),
                'country': data.get('Country'),
                'awards': data.get('Awards'),
                'poster_url': data.get('Poster'),
                'imdb_rating': float(data.get('imdbRating', '0')),
                'imdb_votes': data.get('imdbVotes'),
                'url': f'https://www.imdb.com/title/{imdb_id}/',
                'metascore': data.get('Metascore'),
                'box_office': data.get('BoxOffice'),
                'production': data.get('Production'),
                'is_documentary': 'Documentary' in data.get('Genre', '')
            }
        
        except Exception as e:
            logger.debug(f"Error getting movie details: {e}")
            return None
    
    def search_documentaries(self, topic: str, min_rating: float = 7.0,
                            max_results: int = 10) -> List[Dict]:
        """
        Search for documentaries on a topic
        
        Args:
            topic: Documentary topic
            min_rating: Minimum IMDB rating
            max_results: Max results to return
        
        Returns:
            List of documentaries
        """
        # Search for documentaries
        query = f"{topic} documentary"
        all_movies = self.search_movies(query)
        
        # Filter by rating and type
        documentaries = [
            movie for movie in all_movies
            if movie.get('is_documentary', False) and 
               movie.get('imdb_rating', 0) >= min_rating
        ][:max_results]
        
        logger.info(f"Found {len(documentaries)} documentaries for {topic}")
        return documentaries
    
    def recommend_by_genre(self, genre: str, min_rating: float = 7.5,
                          years: tuple = (2015, 2024)) -> List[Dict]:
        """
        Recommend movies/documentaries by genre
        
        Args:
            genre: Genre (e.g., 'Documentary', 'Biography')
            min_rating: Minimum rating
            years: (start_year, end_year) tuple
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Search by genre and year range
        for year in range(years[1], years[0] - 1, -1):
            movies = self.search_movies(genre, year=year)
            
            # Filter by rating
            filtered = [
                m for m in movies
                if m.get('imdb_rating', 0) >= min_rating and 
                   genre.lower() in [g.lower() for g in m.get('genre', [])]
            ]
            
            recommendations.extend(filtered)
            
            if len(recommendations) >= 10:
                break
        
        # Sort by rating
        recommendations.sort(key=lambda x: x.get('imdb_rating', 0), reverse=True)
        
        return recommendations[:10]
    
    def find_educational_content(self, topic: str) -> List[Dict]:
        """
        Find educational movies and documentaries
        
        Args:
            topic: Educational topic
        
        Returns:
            List of educational content
        """
        queries = [
            f"{topic} documentary",
            f"{topic} explained",
            f"history of {topic}",
            f"{topic} science"
        ]
        
        all_content = []
        seen_ids = set()
        
        for query in queries:
            movies = self.search_movies(query)
            
            for movie in movies:
                imdb_id = movie.get('imdb_id')
                if imdb_id not in seen_ids:
                    seen_ids.add(imdb_id)
                    
                    # Estimate educational value
                    is_educational = (
                        movie.get('is_documentary', False) or
                        'Biography' in movie.get('genre', []) or
                        'History' in movie.get('genre', []) or
                        movie.get('imdb_rating', 0) >= 7.5
                    )
                    
                    if is_educational:
                        movie['educational_score'] = self._calculate_educational_score(movie)
                        all_content.append(movie)
        
        # Sort by educational score
        all_content.sort(key=lambda x: x.get('educational_score', 0), reverse=True)
        
        logger.info(f"Found {len(all_content)} educational items for {topic}")
        return all_content[:20]
    
    def _calculate_educational_score(self, movie: Dict) -> float:
        """Calculate educational value score"""
        score = 0.0
        
        # Base score from rating
        score += movie.get('imdb_rating', 0) * 10
        
        # Genre bonuses
        genre = movie.get('genre', [])
        if 'Documentary' in genre:
            score += 30
        if 'Biography' in genre:
            score += 20
        if 'History' in genre:
            score += 15
        
        # Awards bonus
        if 'Oscar' in movie.get('awards', '') or 'Emmy' in movie.get('awards', ''):
            score += 10
        
        return score


if __name__ == "__main__":
    # Test OMDb API
    logging.basicConfig(level=logging.INFO)
    
    imdb = IMDBDiscovery()
    
    if imdb.api_key:
        print("✅ OMDb API configured")
        
        # Test search
        docs = imdb.search_documentaries("artificial intelligence", min_rating=7.0)
        print(f"\nFound {len(docs)} AI documentaries")
        for doc in docs[:3]:
            print(f"  - {doc['title']} ({doc['year']}) - {doc['imdb_rating']}/10")
    else:
        print("❌ OMDb API key not configured")
        print("Set OMDB_API_KEY environment variable")
        print("Get key from: http://www.omdbapi.com/apikey.aspx")
