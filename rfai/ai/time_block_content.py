"""
Time-Block Content API - Context-aware content delivery
Returns content (YouTube videos, papers, movies) based on current time block
and attentiveness state
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TimeBlockContentManager:
    """
    Manages content delivery based on time blocks and attentiveness
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize content manager
        
        Args:
            config_path: Path to interests.json config
        """
        if config_path is None:
            config_path = Path.cwd() / "interests.json"
        
        self.config_path = config_path
        self.config = self._load_config()
        self.manual_override_block = None  # Manual override
        self.current_block = self._get_current_block()
        
    def _load_config(self) -> Dict:
        """Load configuration from interests.json"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _get_current_block(self) -> Optional[Dict]:
        """
        Determine current time block based on daily schedule
        
        Returns:
            Current time block dict or None if no block active
        """
        # Check for manual override first
        if self.manual_override_block:
            return self.manual_override_block
        
        try:
            # Get timezone from config
            timezone_str = self.config.get('daily_schedule', {}).get('timezone', 'UTC')
            
            # Import timezone support
            from datetime import timezone as tz
            import pytz
            
            # Get current time in configured timezone
            local_tz = pytz.timezone(timezone_str)
            now = datetime.now(local_tz)
            current_time = now.strftime("%H:%M")
            
            schedule = self.config.get('daily_schedule', {}).get('time_blocks', [])
            
            for block in schedule:
                start = block.get('start_time')
                end = block.get('end_time')
                
                # Simple time comparison (assumes no overnight blocks)
                if start <= current_time <= end:
                    return block
            
            return None
        except Exception as e:
            logger.debug(f"Error determining time block: {e}")
            # Fallback to UTC if timezone fails
            try:
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                schedule = self.config.get('daily_schedule', {}).get('time_blocks', [])
                for block in schedule:
                    if block.get('start_time') <= current_time <= block.get('end_time'):
                        return block
            except:
                pass
            return None
    
    def set_manual_override(self, block_name: Optional[str] = None):
        """
        Manually override the current time block
        
        Args:
            block_name: Name of block to activate (e.g., "Science Learning Block")
                       or None to clear override
        """
        if block_name is None:
            self.manual_override_block = None
            logger.info("Manual override cleared - using automatic time detection")
            return
        
        # Find the block by name
        schedule = self.config.get('daily_schedule', {}).get('time_blocks', [])
        for block in schedule:
            if block.get('name') == block_name:
                self.manual_override_block = block
                self.current_block = block
                logger.info(f"Manual override set to: {block_name}")
                return
        
        logger.warning(f"Block '{block_name}' not found in schedule")
    
    def clear_override(self):
        """Clear manual override and return to automatic time detection"""
        self.set_manual_override(None)
        self.current_block = self._get_current_block()
    
    def get_block_info(self) -> Dict:
        """
        Get current time block information
        
        Returns:
            Dict with block details or empty dict if no active block
        """
        if self.current_block:
            return {
                'active': True,
                'name': self.current_block.get('name'),
                'start_time': self.current_block.get('start_time'),
                'end_time': self.current_block.get('end_time'),
                'duration_hours': self.current_block.get('duration_hours'),
                'content_type': self.current_block.get('content_type'),
                'theme': self.current_block.get('theme'),
                'icon': self.current_block.get('icon'),
                'attentiveness_threshold': self.config.get('daily_schedule', {}).get(
                    'attentiveness_threshold', 0.7
                )
            }
        else:
            return {
                'active': False,
                'message': 'No learning block currently active',
                'next_blocks': self._get_next_blocks()
            }
    
    def _get_next_blocks(self) -> List[Dict]:
        """Get next scheduled learning blocks"""
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            schedule = self.config.get('daily_schedule', {}).get('time_blocks', [])
            next_blocks = []
            
            for block in schedule:
                start = block.get('start_time')
                if start > current_time:
                    next_blocks.append({
                        'name': block.get('name'),
                        'start_time': block.get('start_time'),
                        'duration_hours': block.get('duration_hours'),
                        'icon': block.get('icon')
                    })
            
            return next_blocks[:3]  # Return next 3 blocks
        except Exception:
            return []
    
    def get_youtube_content(self) -> Dict:
        """
        Get YouTube content recommendations based on current block
        If no block active, returns combined recommendations from all blocks
        
        Returns:
            Dict with video search queries and channel recommendations
        """
        if not self.current_block:
            # Return combined recommendations from all blocks
            return self._get_all_youtube_content()
        
        content_type = self.current_block.get('content_type')
        
        if content_type == 'science_youtube_and_papers':
            topics = self.config.get('youtube_interests', {}).get('science_topics', [])
            channels = self.config.get('youtube_interests', {}).get('science_channels', [])
            keywords = self.config.get('youtube_interests', {}).get('science_keywords', [])
            return {
                'block': self.current_block.get('name'),
                'type': 'science_learning',
                'topics': topics,
                'channels': channels,
                'keywords': keywords,
                'search_queries': self._generate_search_queries(topics, keywords),
                'quality_indicators': [
                    'Has transcript',
                    'Educational channel',
                    'Mathematical rigor',
                    'Clear explanations'
                ]
            }
        
        elif content_type == 'self_help_youtube':
            topics = self.config.get('youtube_interests', {}).get('self_help_topics', [])
            channels = self.config.get('youtube_interests', {}).get('self_help_channels', [])
            keywords = self.config.get('youtube_interests', {}).get('self_help_keywords', [])
            return {
                'block': self.current_block.get('name'),
                'type': 'self_help_learning',
                'topics': topics,
                'channels': channels,
                'keywords': keywords,
                'search_queries': self._generate_search_queries(topics, keywords),
                'quality_indicators': [
                    'Book-based content',
                    'Actionable advice',
                    'Research-backed',
                    'Clear structure'
                ]
            }
        
        else:
            return {'error': f'Unknown content type: {content_type}'}
    
    def get_movie_content(self) -> Dict:
        """
        Get movie recommendations for cinema block
        If no block active, returns movie recommendations anyway
        
        Returns:
            Dict with movie selection criteria
        """
        content_type = None
        if self.current_block:
            content_type = self.current_block.get('content_type')
        
        if content_type == 'artistic_movies':
            movies = self.config.get('movie_interests', {})
            return {
                'block': self.current_block.get('name') if self.current_block else 'All Blocks',
                'type': 'artistic_cinema',
                'genres': movies.get('genres', []),
                'directors': movies.get('directors', []),
                'criteria': movies.get('criteria', {}),
                'daily_time_hours': movies.get('daily_time_hours', 1.5),
                'post_viewing_review': {
                    'enabled': movies.get('post_viewing_review', True),
                    'questions': [
                        'What was the central theme of this film?',
                        'How did cinematography enhance the storytelling?',
                        'What techniques or artistic choices stood out?',
                        'What did you learn from watching this?',
                        'How did it change your perspective?'
                    ]
                }
            }
        else:
            # Return movie recommendations even if no block active
            movies = self.config.get('movie_interests', {})
            return {
                'block': self.current_block.get('name') if self.current_block else 'All Blocks',
                'type': 'artistic_cinema',
                'genres': movies.get('genres', []),
                'directors': movies.get('directors', []),
                'criteria': movies.get('criteria', {}),
                'daily_time_hours': movies.get('daily_time_hours', 1.5),
                'post_viewing_review': {
                    'enabled': movies.get('post_viewing_review', True),
                    'questions': [
                        'What was the central theme of this film?',
                        'How did cinematography enhance the storytelling?',
                        'What techniques or artistic choices stood out?',
                        'What did you learn from watching this?',
                        'How did it change your perspective?'
                    ]
                }
            }
        
    
    def get_papers_content(self) -> Dict:
        """
        Get research paper recommendations
        If no block active, returns paper recommendations anyway
        
        Returns:
            Dict with ArXiv search parameters
        """
        content_type = None
        if self.current_block:
            content_type = self.current_block.get('content_type')
        
        if content_type == 'science_youtube_and_papers':
            papers = self.config.get('research_paper_interests', {})
            return {
                'block': self.current_block.get('name') if self.current_block else 'Science Block',
                'type': 'research_papers',
                'fields': papers.get('fields', []),
                'arxiv_categories': papers.get('arxiv_categories', []),
                'keywords': papers.get('keywords', []),
                'difficulty_level': papers.get('difficulty_level', 'intermediate'),
                'max_papers_per_day': papers.get('max_papers_per_day', 3),
                'reading_time_per_paper_minutes': 20
            }
        else:
            # Return paper recommendations even if no active science block
            papers = self.config.get('research_paper_interests', {})
            return {
                'block': self.current_block.get('name') if self.current_block else 'All Blocks',
                'type': 'research_papers',
                'fields': papers.get('fields', []),
                'arxiv_categories': papers.get('arxiv_categories', []),
                'keywords': papers.get('keywords', []),
                'difficulty_level': papers.get('difficulty_level', 'intermediate'),
                'max_papers_per_day': papers.get('max_papers_per_day', 3),
                'reading_time_per_paper_minutes': 20
            }
    
    def _generate_search_queries(self, topics: List[str], keywords: List[str]) -> List[str]:
        """
        Generate YouTube search queries
        
        Args:
            topics: List of topics
            keywords: List of quality keywords
        
        Returns:
            List of search query strings
        """
        queries = []
        
        for topic in topics[:5]:  # Limit to 5 topics
            for keyword in keywords[:3]:  # Combine with keywords
                queries.append(f"{topic} {keyword}")
        
        return queries
    
    def get_theme(self) -> Dict:
        """
        Get visual theme for current time block
        
        Returns:
            Dict with color scheme and styling
        """
        if not self.current_block:
            return self._get_default_theme()
        
        theme_name = self.current_block.get('theme', 'default')
        themes = self.config.get('visual_themes', {})
        
        return themes.get(theme_name, self._get_default_theme())
    
    def _get_default_theme(self) -> Dict:
        """Get default theme"""
        return {
            'primary': '#333333',
            'secondary': '#666666',
            'accent': '#0066cc',
            'text': '#ffffff',
            'description': 'Default theme'
        }
    
    def get_progress_goal(self) -> Dict:
        """
        Get current block's progress goal and tracking
        
        Returns:
            Dict with goal information
        """
        if not self.current_block:
            return {'error': 'No active learning block'}
        
        block = self.current_block
        duration = block.get('duration_hours', 1)
        
        return {
            'block_name': block.get('name'),
            'goal_duration_hours': duration,
            'goal_duration_minutes': int(duration * 60),
            'icon': block.get('icon'),
            'attentiveness_required': self.config.get('daily_schedule', {}).get(
                'attentiveness_threshold', 0.7
            ),
            'tracking': {
                'show_timer': True,
                'show_attention_score': True,
                'pause_if_distracted': self.config.get('daily_schedule', {}).get(
                    'pause_if_distracted', False
                ),
                'notify_on_completion': True
            }
        }
    
    def get_full_schedule(self) -> Dict:
        """
        Get the complete daily schedule
        
        Returns:
            Dict with all time blocks and allocation
        """
        schedule = self.config.get('daily_schedule', {})
        allocation = self.config.get('time_allocation', {})
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timezone': schedule.get('timezone', 'UTC'),
            'total_daily_hours': allocation.get('total_daily_hours', 5.5),
            'blocks': schedule.get('time_blocks', []),
            'current_block': self.current_block,
            'next_block': self._get_next_block(),
            'allocation_breakdown': allocation.get('breakdown', {})
        }
    
    def _get_next_block(self) -> Optional[Dict]:
        """Get next scheduled time block"""
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            schedule = self.config.get('daily_schedule', {}).get('time_blocks', [])
            
            for block in schedule:
                start = block.get('start_time')
                if start > current_time:
                    return {
                        'name': block.get('name'),
                        'start_time': block.get('start_time'),
                        'duration_hours': block.get('duration_hours'),
                        'icon': block.get('icon')
                    }
            
            return None
        except Exception:
            return None    
    def _get_all_youtube_content(self) -> Dict:
        """
        Get combined YouTube recommendations from all blocks when no block is active
        
        Returns:
            Dict with combined video recommendations
        """
        all_topics = []
        all_channels = []
        all_keywords = []
        
        # Science block content
        all_topics.extend(self.config.get('youtube_interests', {}).get('science_topics', []))
        all_channels.extend(self.config.get('youtube_interests', {}).get('science_channels', []))
        all_keywords.extend(self.config.get('youtube_interests', {}).get('science_keywords', []))
        
        # Self-help block content
        all_topics.extend(self.config.get('youtube_interests', {}).get('self_help_topics', []))
        all_channels.extend(self.config.get('youtube_interests', {}).get('self_help_channels', []))
        all_keywords.extend(self.config.get('youtube_interests', {}).get('self_help_keywords', []))
        
        return {
            'block': 'All Blocks - No Specific Block Active',
            'type': 'combined_learning',
            'topics': list(set(all_topics)),  # Remove duplicates
            'channels': list(set(all_channels)),
            'keywords': list(set(all_keywords)),
            'search_queries': self._generate_search_queries(
                list(set(all_topics)), 
                list(set(all_keywords))
            ),
            'quality_indicators': [
                'Has transcript',
                'Educational content',
                'Clear explanations',
                'Actionable insights'
            ],
            'note': 'Showing recommendations from all time blocks'
        }