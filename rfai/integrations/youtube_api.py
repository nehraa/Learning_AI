"""
YouTube API Integration
Discovers educational videos based on learning topics
"""

import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class YouTubeDiscovery:
    """
    YouTube content discovery using YouTube Data API v3
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube discovery
        
        Args:
            api_key: YouTube Data API key (get from Google Cloud Console)
        """
        self.api_key = api_key or os.environ.get('YOUTUBE_API_KEY')
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        if not self.api_key:
            logger.warning("No YouTube API key provided - functionality limited")
        else:
            logger.info("YouTube API initialized")
    
    def search_videos(self, query: str, max_results: int = 10, 
                     duration: str = 'medium', order: str = 'relevance',
                     published_after: str = None) -> List[Dict]:
        """
        Search for videos
        
        Args:
            query: Search query
            max_results: Max videos to return (1-50)
            duration: 'short' (<4min), 'medium' (4-20min), 'long' (>20min), 'any'
            order: 'relevance', 'rating', 'viewCount', 'date'
            published_after: ISO 8601 timestamp (e.g., '2024-01-01T00:00:00Z')
        
        Returns:
            List of video dicts with metadata
        """
        if not self.api_key:
            logger.error("YouTube API key not configured")
            return []
        
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': min(max_results, 50),
            'order': order,
            'videoDefinition': 'high',
            'key': self.api_key
        }
        
        if duration != 'any':
            params['videoDuration'] = duration
        
        if published_after:
            params['publishedAfter'] = published_after
        
        try:
            response = requests.get(f"{self.base_url}/search", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                # Get additional details (duration, stats)
                video_details = self._get_video_details(video_id)
                
                videos.append({
                    'id': f'youtube_{video_id}',
                    'video_id': video_id,
                    'type': 'video',
                    'source': 'youtube',
                    'title': snippet['title'],
                    'description': snippet['description'],
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'channel': snippet['channelTitle'],
                    'published_at': snippet['publishedAt'],
                    'duration_seconds': video_details.get('duration_seconds'),
                    'view_count': video_details.get('view_count'),
                    'like_count': video_details.get('like_count'),
                    'tags': snippet.get('tags', []),
                    'difficulty': self._estimate_difficulty(snippet, video_details)
                })
            
            logger.info(f"Found {len(videos)} videos for query: {query}")
            return videos
        
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return []
    
    def _get_video_details(self, video_id: str) -> Dict:
        """Get detailed info about a video"""
        if not self.api_key:
            return {}
        
        try:
            params = {
                'part': 'contentDetails,statistics',
                'id': video_id,
                'key': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/videos", params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('items'):
                return {}
            
            item = data['items'][0]
            content = item.get('contentDetails', {})
            stats = item.get('statistics', {})
            
            # Parse ISO 8601 duration (PT15M33S)
            duration = content.get('duration', 'PT0S')
            duration_seconds = self._parse_duration(duration)
            
            return {
                'duration_seconds': duration_seconds,
                'view_count': int(stats.get('viewCount', 0)),
                'like_count': int(stats.get('likeCount', 0)),
                'comment_count': int(stats.get('commentCount', 0))
            }
        
        except Exception as e:
            logger.debug(f"Error getting video details: {e}")
            return {}
    
    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        import re
        
        # PT15M33S -> 933 seconds
        hours = re.search(r'(\d+)H', duration)
        minutes = re.search(r'(\d+)M', duration)
        seconds = re.search(r'(\d+)S', duration)
        
        total = 0
        if hours:
            total += int(hours.group(1)) * 3600
        if minutes:
            total += int(minutes.group(1)) * 60
        if seconds:
            total += int(seconds.group(1))
        
        return total
    
    def _estimate_difficulty(self, snippet: Dict, details: Dict) -> str:
        """Estimate video difficulty based on metadata"""
        title = snippet.get('title', '').lower()
        desc = snippet.get('description', '').lower()
        
        # Check for beginner indicators
        beginner_words = ['intro', 'introduction', 'beginner', 'basics', 'getting started', 
                         'tutorial', 'explained', '101', 'for beginners']
        if any(word in title or word in desc for word in beginner_words):
            return 'beginner'
        
        # Check for advanced indicators
        advanced_words = ['advanced', 'deep dive', 'expert', 'masterclass', 'phd', 
                         'research', 'optimization', 'production']
        if any(word in title or word in desc for word in advanced_words):
            return 'advanced'
        
        # Default to intermediate
        return 'intermediate'
    
    def search_by_topic(self, topic: str, subtopics: List[str] = None,
                       max_per_topic: int = 5) -> List[Dict]:
        """
        Search for videos across multiple subtopics
        
        Args:
            topic: Main topic
            subtopics: List of subtopics
            max_per_topic: Max videos per subtopic
        
        Returns:
            Combined list of videos
        """
        all_videos = []
        
        # Search main topic
        main_query = f"{topic} tutorial explained"
        all_videos.extend(self.search_videos(main_query, max_results=max_per_topic))
        
        # Search subtopics
        if subtopics:
            for subtopic in subtopics[:5]:  # Limit to 5 subtopics
                query = f"{topic} {subtopic} tutorial"
                videos = self.search_videos(query, max_results=max_per_topic)
                all_videos.extend(videos)
        
        # Remove duplicates
        seen_ids = set()
        unique_videos = []
        for video in all_videos:
            if video['video_id'] not in seen_ids:
                seen_ids.add(video['video_id'])
                unique_videos.append(video)
        
        logger.info(f"Found {len(unique_videos)} unique videos for topic: {topic}")
        return unique_videos
    
    def get_channel_videos(self, channel_id: str, max_results: int = 10) -> List[Dict]:
        """
        Get videos from a specific channel
        
        Args:
            channel_id: YouTube channel ID
            max_results: Max videos to return
        
        Returns:
            List of videos
        """
        if not self.api_key:
            return []
        
        try:
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'maxResults': max_results,
                'order': 'date',
                'type': 'video',
                'key': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/search", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                videos.append({
                    'id': f'youtube_{video_id}',
                    'video_id': video_id,
                    'title': snippet['title'],
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'channel': snippet['channelTitle'],
                    'published_at': snippet['publishedAt']
                })
            
            return videos
        
        except Exception as e:
            logger.error(f"Channel videos error: {e}")
            return []


if __name__ == "__main__":
    # Test YouTube API
    logging.basicConfig(level=logging.INFO)
    
    yt = YouTubeDiscovery()
    
    if yt.api_key:
        videos = yt.search_videos("machine learning tutorial", max_results=3)
        print(f"\n✅ Found {len(videos)} videos")
        for v in videos:
            print(f"  - {v['title'][:60]}... ({v['duration_seconds']}s)")
    else:
        print("❌ YouTube API key not configured")
        print("Set YOUTUBE_API_KEY environment variable")
        print("Get key from: https://console.cloud.google.com/apis/credentials")
