"""
Time-Block Access Control Manager
Implements soft-lock system: when block is active, lock to block content
when no block is active, free access to all content
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class BlockAccessManager:
    """
    Manages content access based on time blocks
    - Active block: locked to block content only, must reach attention goal
    - No active block: full free access to all content types
    """
    
    def __init__(self, config_path: Optional[Path] = None, db_path: Optional[Path] = None):
        """
        Initialize access manager
        
        Args:
            config_path: Path to interests.json
            db_path: Path to database
        """
        if config_path is None:
            config_path = Path.cwd() / "interests.json"
        if db_path is None:
            db_path = Path.home() / ".rfai" / "data" / "rfai.db"
        
        self.config_path = config_path
        self.db_path = db_path
        self.config = self._load_config()
        self.current_block = self._get_current_block()
        self.is_locked = False
        self.lock_reason = None
        
    def _load_config(self) -> Dict:
        """Load configuration from interests.json"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _get_current_block(self) -> Optional[Dict]:
        """Get currently active time block based on current time"""
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            schedule = self.config.get('daily_schedule', {}).get('time_blocks', [])
            
            for block in schedule:
                start = block.get('start_time')
                end = block.get('end_time')
                
                if start <= current_time <= end:
                    return block
            
            return None
        except Exception:
            return None
    
    def get_access_status(self) -> Dict:
        """
        Get current access control status
        
        Returns:
            Dict with lock status, allowed content, and messaging
        """
        self.current_block = self._get_current_block()
        
        if self.current_block:
            # Check if active session exists and needs attention goal
            session_id = self._get_active_session_id()
            
            if session_id:
                attention_avg = self._get_session_attention(session_id)
                threshold = self.config.get('daily_schedule', {}).get('attentiveness_threshold', 0.7)
                goal_met = attention_avg >= (threshold * 100) if attention_avg else False
                
                self.is_locked = not goal_met
                self.lock_reason = f"Attentiveness goal not met ({int(attention_avg or 0)}% / {int(threshold * 100)}%)"
                
                return {
                    'has_active_block': True,
                    'block_name': self.current_block.get('name'),
                    'block_type': self.current_block.get('content_type'),
                    'locked': self.is_locked,
                    'lock_reason': self.lock_reason if self.is_locked else None,
                    'allowed_content_types': self._get_allowed_content_types(),
                    'goal_met': goal_met,
                    'current_attention': attention_avg,
                    'required_attention': threshold * 100,
                    'message': 'BLOCK LOCKED - Keep learning until goal met' if self.is_locked 
                              else 'Block goal met - You can take a break or access other content'
                }
            else:
                return {
                    'has_active_block': True,
                    'block_name': self.current_block.get('name'),
                    'block_type': self.current_block.get('content_type'),
                    'locked': False,
                    'lock_reason': None,
                    'allowed_content_types': self._get_allowed_content_types(),
                    'message': f"Start your {self.current_block.get('name')} session to begin tracking"
                }
        else:
            # No active block - free access to everything
            self.is_locked = False
            self.lock_reason = None
            
            return {
                'has_active_block': False,
                'locked': False,
                'lock_reason': None,
                'allowed_content_types': ['youtube_self_help', 'youtube_science', 'papers', 'movies'],
                'message': 'No active learning block - Free access to all content',
                'next_block': self._get_next_block()
            }
    
    def _get_active_session_id(self) -> Optional[int]:
        """Get ID of active session for current block"""
        try:
            if not self.current_block:
                return None
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id FROM time_block_sessions
                WHERE block_name = ? AND end_time IS NULL
                ORDER BY start_time DESC
                LIMIT 1
            """, (self.current_block.get('name'),))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            logger.debug(f"Error getting session ID: {e}")
            return None
    
    def _get_session_attention(self, session_id: int) -> Optional[float]:
        """Get average attention for a session"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT AVG(score) FROM attention_log
                WHERE timestamp >= (
                    SELECT start_time FROM time_block_sessions WHERE id = ?
                ) AND timestamp <= COALESCE(
                    (SELECT end_time FROM time_block_sessions WHERE id = ?),
                    datetime('now')
                )
            """, (session_id, session_id))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else None
        except Exception as e:
            logger.debug(f"Error getting session attention: {e}")
            return None
    
    def _get_allowed_content_types(self) -> List[str]:
        """Get content types allowed in current block"""
        if not self.current_block:
            return ['youtube_self_help', 'youtube_science', 'papers', 'movies']
        
        block_type = self.current_block.get('content_type', '')
        
        if 'science' in block_type:
            return ['youtube_science', 'papers']
        elif 'self_help' in block_type:
            return ['youtube_self_help']
        elif 'movie' in block_type:
            return ['movies']
        else:
            return ['youtube_science', 'youtube_self_help', 'papers', 'movies']
    
    def _get_next_block(self) -> Optional[Dict]:
        """Get next scheduled block"""
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
    
    def can_access_content(self, content_type: str) -> bool:
        """
        Check if user can access specific content type
        
        Args:
            content_type: Type of content ('youtube_science', 'papers', 'movies', etc)
        
        Returns:
            True if access allowed, False if locked
        """
        status = self.get_access_status()
        
        if status['locked']:
            return False
        
        allowed = status.get('allowed_content_types', [])
        return content_type in allowed
    
    def log_activity(self, session_id: int, action: str, content_type: str = None, page_title: str = None):
        """Log user activity during a block session"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get current attention score
            cursor.execute("""
                SELECT score FROM attention_log
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            attention_result = cursor.fetchone()
            attention_score = attention_result[0] if attention_result else None
            
            cursor.execute("""
                INSERT INTO block_activity_log (
                    session_id, timestamp, action, content_type, 
                    page_title, attention_score
                ) VALUES (?, datetime('now'), ?, ?, ?, ?)
            """, (session_id, action, content_type, page_title, attention_score))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Error logging activity: {e}")
    
    def get_block_progress(self, session_id: int) -> Dict:
        """Get progress toward block completion goal"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute("""
                SELECT goal_duration_minutes, start_time FROM time_block_sessions
                WHERE id = ?
            """, (session_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'error': 'Session not found'}
            
            goal_minutes, start_time = result
            
            # Calculate elapsed time
            from datetime import datetime as dt
            start_dt = dt.fromisoformat(start_time)
            elapsed_minutes = (dt.now() - start_dt).total_seconds() / 60
            
            # Get average attention
            cursor.execute("""
                SELECT AVG(score) FROM attention_log
                WHERE timestamp >= ? AND timestamp <= datetime('now')
            """, (start_time,))
            
            attention_result = cursor.fetchone()
            avg_attention = attention_result[0] if attention_result and attention_result[0] else 0
            
            conn.close()
            
            threshold = self.config.get('daily_schedule', {}).get('attentiveness_threshold', 0.7)
            attention_met = (avg_attention / 100) >= threshold
            
            return {
                'goal_duration_minutes': goal_minutes,
                'elapsed_minutes': int(elapsed_minutes),
                'progress_percent': min(100, int((elapsed_minutes / goal_minutes) * 100)) if goal_minutes else 0,
                'average_attention': int(avg_attention),
                'attention_threshold': int(threshold * 100),
                'attention_met': attention_met,
                'can_end_session': attention_met or (elapsed_minutes >= goal_minutes * 1.5)  # Can end if 50% over time
            }
        except Exception as e:
            logger.error(f"Error getting block progress: {e}")
            return {'error': str(e)}
