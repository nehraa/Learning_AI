"""
Content Scheduler
Implements the 3-hour daily learning plan with time-blocked content allocation
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, time

from rfai.integrations.youtube_api import YouTubeDiscovery
from rfai.integrations.arxiv_api import ArXivDiscovery
from rfai.integrations.edx_api import EdXDiscovery
from rfai.integrations.imdb_api import IMDBDiscovery
from rfai.ai.plan_parser import LearningPlanParser

logger = logging.getLogger(__name__)


class ContentScheduler:
    """
    Schedules content according to the 3-hour daily plan:
    - 1 hour: YouTube (learning-borderline entertainment)
    - 1-2 hours: Artistic movies
    - 1 hour: Research papers
    """
    
    def __init__(self, interests_file: str = "interests.json",
                 plan_file: str = "daily_3hr_plan.md"):
        """
        Initialize content scheduler
        
        Args:
            interests_file: Path to interests configuration
            plan_file: Path to learning plan
        """
        self.interests = self._load_interests(interests_file)
        self.plan_parser = LearningPlanParser(plan_file)
        
        # Initialize integrations
        self.youtube = YouTubeDiscovery()
        self.arxiv = ArXivDiscovery()
        self.edx = EdXDiscovery()
        self.imdb = IMDBDiscovery()
        
        # Get time allocations from interests
        self.time_allocation = self.interests.get('time_allocation', {})
        self.youtube_hours = self.time_allocation.get('breakdown', {}).get('youtube_learning', 1.0)
        self.movie_hours = self.time_allocation.get('breakdown', {}).get('artistic_movies', 1.5)
        self.paper_hours = self.time_allocation.get('breakdown', {}).get('research_papers', 1.0)
        
        logger.info(f"Content scheduler initialized: {self.youtube_hours}h YouTube, "
                   f"{self.movie_hours}h movies, {self.paper_hours}h papers")
    
    def _load_interests(self, interests_file: str) -> Dict:
        """Load user interests configuration"""
        try:
            file_path = Path(interests_file)
            if not file_path.exists():
                # Try relative to project root
                project_root = Path(__file__).parent.parent.parent
                file_path = project_root / interests_file
            
            with open(file_path, 'r') as f:
                interests = json.load(f)
            
            logger.info(f"Loaded interests from {file_path}")
            return interests
        except Exception as e:
            logger.error(f"Error loading interests: {e}")
            return {}
    
    def generate_daily_schedule(self, date: Optional[datetime] = None) -> Dict:
        """
        Generate complete daily schedule
        
        Args:
            date: Date to schedule for (default: today)
        
        Returns:
            Dict with scheduled content for all time blocks
        """
        if date is None:
            date = datetime.now()
        
        logger.info(f"Generating schedule for {date.date()}")
        
        # Get current learning plan day
        current_day_plan = self.plan_parser.get_current_day_plan()
        
        # Get interests
        youtube_interests = self.interests.get('youtube_interests', {})
        paper_interests = self.interests.get('research_paper_interests', {})
        movie_interests = self.interests.get('movie_interests', {})
        
        schedule = {
            'date': date.isoformat(),
            'total_hours': self.youtube_hours + self.movie_hours + self.paper_hours,
            'learning_plan': current_day_plan,
            'content_blocks': []
        }
        
        # Block 1: YouTube Learning (1 hour)
        youtube_block = self._schedule_youtube_block(youtube_interests, current_day_plan)
        schedule['content_blocks'].append(youtube_block)
        
        # Block 2: Research Papers (1 hour)
        paper_block = self._schedule_paper_block(paper_interests, current_day_plan)
        schedule['content_blocks'].append(paper_block)
        
        # Block 3: Artistic Movie (1-2 hours)
        movie_block = self._schedule_movie_block(movie_interests)
        schedule['content_blocks'].append(movie_block)
        
        logger.info(f"Generated schedule with {len(schedule['content_blocks'])} content blocks")
        return schedule
    
    def _schedule_youtube_block(self, interests: Dict, 
                               day_plan: Optional[Dict]) -> Dict:
        """
        Schedule YouTube learning block (1 hour)
        
        Args:
            interests: YouTube interests configuration
            day_plan: Current day's learning plan
        
        Returns:
            YouTube content block
        """
        # Get search topics
        topics = interests.get('topics', [])
        content_style = interests.get('content_style', 'learning_borderline_entertainment')
        
        # If we have a current day plan, use its topic
        if day_plan:
            topics = [day_plan['topic']] + topics
        
        # Search for videos
        videos = []
        for topic in topics[:3]:  # Limit to top 3 topics
            topic_videos = self.youtube.search_educational_videos(
                topic,
                max_results=2,
                include_borderline=(content_style == 'learning_borderline_entertainment')
            )
            videos.extend(topic_videos)
        
        # Remove duplicates
        seen = set()
        unique_videos = []
        for video in videos:
            if video['video_id'] not in seen:
                seen.add(video['video_id'])
                unique_videos.append(video)
        
        return {
            'type': 'youtube',
            'duration_hours': self.youtube_hours,
            'duration_minutes': int(self.youtube_hours * 60),
            'content_style': content_style,
            'videos': unique_videos[:5],  # Top 5 recommendations
            'description': 'Educational YouTube content (learning-borderline entertainment)',
            'completion_required': False,
            'post_activity': None
        }
    
    def _schedule_paper_block(self, interests: Dict,
                             day_plan: Optional[Dict]) -> Dict:
        """
        Schedule research paper block (1 hour)
        
        Args:
            interests: Paper interests configuration
            day_plan: Current day's learning plan
        
        Returns:
            Paper content block
        """
        # Get search topics
        fields = interests.get('fields', [])
        keywords = interests.get('keywords', [])
        categories = interests.get('arxiv_categories', [])
        
        # If we have a current day plan, use its topic
        search_topics = []
        if day_plan:
            search_topics.append(day_plan['topic'])
        search_topics.extend(keywords[:2])
        
        # Search for papers
        papers = self.arxiv.search_by_topics(
            search_topics,
            max_per_topic=2,
            categories=categories if categories else None
        )
        
        return {
            'type': 'research_papers',
            'duration_hours': self.paper_hours,
            'duration_minutes': int(self.paper_hours * 60),
            'papers': papers[:3],  # Top 3 papers
            'description': 'Research paper reading and analysis',
            'completion_required': False,
            'post_activity': None
        }
    
    def _schedule_movie_block(self, interests: Dict) -> Dict:
        """
        Schedule artistic movie block (1-2 hours)
        
        Args:
            interests: Movie interests configuration
        
        Returns:
            Movie content block
        """
        style = interests.get('style', 'artistic_film_school')
        genres = interests.get('genres', [])
        directors = interests.get('directors', [])
        
        # Search for artistic films
        movies = []
        
        # Search by director if specified
        for director in directors[:3]:
            director_films = self.imdb.search_artistic_films(
                query=director,
                max_results=2,
                min_rating=7.0
            )
            movies.extend(director_films)
        
        # General artistic film search
        if len(movies) < 5:
            general_films = self.imdb.search_artistic_films(
                max_results=5,
                min_rating=7.0
            )
            movies.extend(general_films)
        
        # Remove duplicates
        seen = set()
        unique_movies = []
        for movie in movies:
            if movie['imdb_id'] not in seen:
                seen.add(movie['imdb_id'])
                unique_movies.append(movie)
        
        # Check if post-viewing review is required
        post_viewing_required = interests.get('post_viewing_review', True)
        
        return {
            'type': 'artistic_movie',
            'duration_hours': self.movie_hours,
            'duration_minutes': int(self.movie_hours * 60),
            'style': style,
            'movies': unique_movies[:5],  # Top 5 recommendations
            'description': 'Artistic/film-school worthy cinema',
            'completion_required': True,
            'post_activity': {
                'type': 'review_prompt',
                'required': post_viewing_required,
                'questions': [
                    'What was the central theme or message of the film?',
                    'How did the cinematography contribute to the storytelling?',
                    'What techniques did the director use that stood out?',
                    'How does this film compare to others you\'ve seen?',
                    'What did you learn from this film?'
                ]
            } if post_viewing_required else None
        }
    
    def get_schedule_summary(self, schedule: Dict) -> str:
        """
        Get a text summary of the schedule
        
        Args:
            schedule: Schedule dict from generate_daily_schedule
        
        Returns:
            Formatted text summary
        """
        lines = [
            f"📅 Daily Learning Schedule",
            f"Date: {schedule['date']}",
            f"Total Time: {schedule['total_hours']} hours",
            ""
        ]
        
        if schedule.get('learning_plan'):
            plan = schedule['learning_plan']
            lines.append(f"📚 Today's Topic: {plan['topic']}")
            lines.append(f"Week {plan['week']}, Day {plan['day']}")
            lines.append("")
        
        for i, block in enumerate(schedule['content_blocks'], 1):
            lines.append(f"Block {i}: {block['type'].upper()} ({block['duration_hours']}h)")
            lines.append(f"  {block['description']}")
            
            if block['type'] == 'youtube':
                lines.append(f"  Videos: {len(block['videos'])} recommendations")
            elif block['type'] == 'research_papers':
                lines.append(f"  Papers: {len(block['papers'])} recommendations")
            elif block['type'] == 'artistic_movie':
                lines.append(f"  Movies: {len(block['movies'])} recommendations")
                if block.get('post_activity'):
                    lines.append("  Post-viewing review: REQUIRED")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_current_block(self, schedule: Dict) -> Optional[Dict]:
        """
        Determine which content block should be active now
        
        Args:
            schedule: Schedule dict
        
        Returns:
            Current block or None
        """
        # Simple implementation - could be enhanced with actual time tracking
        current_hour = datetime.now().hour
        
        # Example: Morning = YouTube, Afternoon = Papers, Evening = Movies
        if 9 <= current_hour < 12:
            return schedule['content_blocks'][0]  # YouTube
        elif 14 <= current_hour < 17:
            return schedule['content_blocks'][1]  # Papers
        elif 19 <= current_hour < 22:
            return schedule['content_blocks'][2]  # Movies
        
        return None


if __name__ == "__main__":
    # Test content scheduler
    logging.basicConfig(level=logging.INFO)
    
    scheduler = ContentScheduler()
    
    # Generate today's schedule
    schedule = scheduler.generate_daily_schedule()
    
    # Print summary
    print("\n" + "="*60)
    print(scheduler.get_schedule_summary(schedule))
    print("="*60)
    
    # Show current block
    current = scheduler.get_current_block(schedule)
    if current:
        print(f"\n📍 Current Block: {current['type'].upper()}")
        print(f"Duration: {current['duration_hours']} hours")
