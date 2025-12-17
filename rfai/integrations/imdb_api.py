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
    
    def classify_artistic_merit(self, movie: Dict) -> str:
        """
        Classify movie as artistic/film-school worthy vs generic entertainment
        
        Returns:
            'artistic' - Film school quality, artistic merit
            'good_generic' - Well-rated but generic/commercial
            'entertainment' - Pure entertainment
        """
        title = movie.get('title', '').lower()
        plot = movie.get('plot', '').lower()
        director = movie.get('director', '').lower()
        genre = movie.get('genre', [])
        awards = movie.get('awards', '')
        rating = movie.get('imdb_rating', 0)
        
        # Prestigious/artistic directors
        artistic_directors = [
            'andrei tarkovsky', 'ingmar bergman', 'akira kurosawa', 'stanley kubrick',
            'terrence malick', 'wong kar-wai', 'federico fellini', 'jean-luc godard',
            'francois truffaut', 'yasujiro ozu', 'krzysztof kieslowski', 'david lynch',
            'wes anderson', 'paul thomas anderson', 'christopher nolan', 'denis villeneuve',
            'alfonso cuaron', 'alejandro iñárritu', 'park chan-wook', 'bong joon-ho'
        ]
        
        # Artistic genres
        artistic_genres = [
            'Drama', 'Mystery', 'Thriller', 'War', 'Biography', 'History'
        ]
        
        # Generic/commercial genres (lower artistic merit typically)
        commercial_genres = [
            'Action', 'Comedy', 'Romance', 'Horror', 'Fantasy'
        ]
        
        # Check for prestigious awards
        has_major_awards = any(award in awards for award in [
            'Oscar', 'Academy Award', 'Golden Globe', 'Cannes', 'Venice', 
            'Berlin', 'Palme', 'Golden Lion', 'Golden Bear'
        ])
        
        # Check for artistic director
        is_artistic_director = any(dir in director for dir in artistic_directors)
        
        # Check for foreign/art house indicators
        is_foreign = movie.get('country', '') not in ['USA', 'United States', 'UK', 'United Kingdom']
        
        # Calculate artistic score
        artistic_score = 0
        
        if is_artistic_director:
            artistic_score += 50
        
        if has_major_awards:
            artistic_score += 30
        
        if is_foreign:
            artistic_score += 20
        
        # Genre scoring
        for g in genre:
            if g in artistic_genres:
                artistic_score += 10
            elif g in commercial_genres:
                artistic_score -= 10
        
        # High critical acclaim but not blockbuster
        metascore = movie.get('metascore')
        if metascore and metascore != 'N/A':
            try:
                if int(metascore) >= 80:
                    artistic_score += 20
            except:
                pass
        
        # Classify based on score
        if artistic_score >= 50:
            return 'artistic'
        elif rating >= 7.5 and artistic_score >= 20:
            return 'artistic'
        elif rating >= 7.0:
            return 'good_generic'
        else:
            return 'entertainment'
    
    def search_artistic_films(self, query: str = None, max_results: int = 10,
                             min_rating: float = 7.0) -> List[Dict]:
        """
        Search for artistic/film-school worthy movies
        
        Args:
            query: Search query (optional)
            max_results: Max films to return
            min_rating: Minimum IMDB rating
        
        Returns:
            List of artistic films with classification
        """
        # If no query, use curated list of artistic films
        if not query:
            queries = [
                'tarkovsky', 'bergman', 'kurosawa', 'fellini',
                'criterion collection', 'foreign cinema', 'art house'
            ]
        else:
            queries = [query]
        
        all_films = []
        seen_ids = set()
        
        for q in queries:
            movies = self.search_movies(q)
            
            for movie in movies:
                imdb_id = movie.get('imdb_id')
                if imdb_id not in seen_ids:
                    seen_ids.add(imdb_id)
                    
                    # Classify artistic merit
                    movie['artistic_classification'] = self.classify_artistic_merit(movie)
                    movie['artistic_score'] = self._calculate_artistic_score(movie)
                    
                    # Only include artistic or good_generic with high rating
                    if (movie['artistic_classification'] == 'artistic' or
                        (movie['artistic_classification'] == 'good_generic' and 
                         movie.get('imdb_rating', 0) >= min_rating)):
                        all_films.append(movie)
        
        # Sort by artistic score
        all_films.sort(key=lambda x: x.get('artistic_score', 0), reverse=True)
        
        logger.info(f"Found {len(all_films)} artistic films")
        return all_films[:max_results]
    
    def search_by_director(self, director: str, min_rating: float = 7.0,
                          max_results: int = 10) -> List[Dict]:
        """
        Search for movies by a specific director
        
        Args:
            director: Director name
            min_rating: Minimum IMDB rating
            max_results: Max results to return
        
        Returns:
            List of movies by director, sorted by rating
        """
        try:
            # Search for the director's name
            movies = self.search_movies(director)
            
            if not movies:
                logger.warning(f"No movies found for director: {director}")
                return []
            
            # Filter to high-rated films
            filtered = [
                m for m in movies
                if m.get('imdb_rating', 0) >= min_rating
            ]
            
            # Sort by rating descending
            filtered.sort(key=lambda x: x.get('imdb_rating', 0), reverse=True)
            
            logger.info(f"Found {len(filtered)} movies by {director} with rating >= {min_rating}")
            return filtered[:max_results]
        
        except Exception as e:
            logger.error(f"Error searching for director {director}: {e}")
            return []
    
    def _calculate_artistic_score(self, movie: Dict) -> float:
        """Calculate artistic merit score for ranking"""
        score = 0.0
        
        # Base rating (max 100 points)
        score += movie.get('imdb_rating', 0) * 10
        
        # Metascore bonus
        metascore = movie.get('metascore')
        if metascore and metascore != 'N/A':
            try:
                score += int(metascore) * 0.5
            except:
                pass
        
        # Awards (max 50 points)
        awards = movie.get('awards', '').lower()
        if 'oscar' in awards or 'academy award' in awards:
            score += 30
        if 'cannes' in awards or 'palme' in awards:
            score += 25
        if 'venice' in awards or 'golden lion' in awards:
            score += 20
        if 'golden globe' in awards:
            score += 15
        
        # Classification bonus
        classification = movie.get('artistic_classification', 'entertainment')
        if classification == 'artistic':
            score += 40
        elif classification == 'good_generic':
            score += 10
        
        return score
    
    def recommend_for_study(self, focus_area: str = 'cinematography',
                           max_results: int = 5) -> List[Dict]:
        """
        Recommend films for study (cinematography, narrative, etc.)
        
        Args:
            focus_area: What to study ('cinematography', 'narrative', 'experimental')
            max_results: Max films to return
        
        Returns:
            List of films recommended for study
        """
        focus_queries = {
            'cinematography': ['deakins', 'lubezki', 'visual', 'cinematography'],
            'narrative': ['kubrick', 'nolan', 'complex narrative', 'non-linear'],
            'experimental': ['lynch', 'tarkovsky', 'experimental', 'avant-garde'],
            'character': ['character study', 'method acting', 'performance'],
            'editing': ['editing', 'montage', 'rhythm']
        }
        
        queries = focus_queries.get(focus_area, ['film school', 'essential cinema'])
        
        recommendations = []
        for query in queries:
            films = self.search_artistic_films(query, max_results=2)
            recommendations.extend(films)
        
        # Remove duplicates
        seen = set()
        unique = []
        for film in recommendations:
            if film['imdb_id'] not in seen:
                seen.add(film['imdb_id'])
                unique.append(film)
        
        return unique[:max_results]


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
