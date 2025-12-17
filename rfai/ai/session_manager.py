"""
Session Manager - Track learning block sessions with attention goals
Ensures content stays locked to block until attention threshold is met
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import sqlite3

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages learning block sessions with:
    - Content locking (only current block content shown)
    - Attention goal tracking
    - Data collection for AI training
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize session manager"""
        if db_path is None:
            data_dir = Path.home() / ".rfai" / "data"
            db_path = data_dir / "rfai.db"
        
        self.db_path = db_path
        self.current_session = None
    
    def start_session(self, block_name: str, block_type: str, 
                     goal_duration_minutes: int, 
                     attentiveness_threshold: float = 0.7) -> Dict:
        """
        Start a new learning block session
        
        Args:
            block_name: Name of block (e.g., "Science Learning Block")
            block_type: Type (science_youtube_and_papers|self_help_youtube|artistic_movies)
            goal_duration_minutes: Target minutes for this block
            attentiveness_threshold: Attention score needed (0-1)
        
        Returns:
            Session dict with ID and metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            session_id = f"{block_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            cursor.execute("""
                INSERT INTO time_block_sessions (
                    block_name, block_type, start_time, goal_duration_minutes
                ) VALUES (?, ?, datetime('now'), ?)
            """, (block_name, block_type, goal_duration_minutes))
            
            conn.commit()
            db_session_id = cursor.lastrowid
            conn.close()
            
            self.current_session = {
                'id': db_session_id,
                'session_id': session_id,
                'block_name': block_name,
                'block_type': block_type,
                'goal_duration_minutes': goal_duration_minutes,
                'attentiveness_threshold': attentiveness_threshold,
                'start_time': datetime.now(),
                'content_shown': [],
                'attention_scores': []
            }
            
            logger.info(f"✅ Session started: {block_name} ({goal_duration_minutes}m, {attentiveness_threshold*100:.0f}% attention)")
            
            return {
                'success': True,
                'session_id': db_session_id,
                'message': f'Session started for {block_name}'
            }
        
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_current_session(self) -> Optional[Dict]:
        """Get current active session"""
        return self.current_session
    
    def is_session_complete(self, avg_attention: float) -> Dict:
        """
        Check if session is complete
        
        Returns dict with:
        - is_complete: bool
        - reason: str
        - metrics: dict of session stats
        """
        if not self.current_session:
            return {'is_complete': False, 'reason': 'No active session'}
        
        elapsed = (datetime.now() - self.current_session['start_time']).total_seconds() / 60
        goal = self.current_session['goal_duration_minutes']
        threshold = self.current_session['attentiveness_threshold']
        
        metrics = {
            'elapsed_minutes': round(elapsed, 1),
            'goal_minutes': goal,
            'average_attention': round(avg_attention, 2),
            'threshold': threshold,
            'time_progress': round((elapsed / goal) * 100, 1),
            'attention_progress': round((avg_attention / threshold) * 100, 1)
        }
        
        # Complete if both time AND attention goals met
        time_complete = elapsed >= goal
        attention_complete = avg_attention >= threshold
        
        return {
            'is_complete': time_complete and attention_complete,
            'time_met': time_complete,
            'attention_met': attention_complete,
            'metrics': metrics,
            'message': (
                f"Time: {metrics['elapsed_minutes']:.0f}/{goal}m, "
                f"Attention: {metrics['average_attention']:.0%}/{threshold:.0%}"
            )
        }
    
    def record_content_shown(self, content_id: str, content_type: str, 
                            title: str, metadata: Dict = None):
        """Record that content was shown during this session"""
        if not self.current_session:
            return
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'content_id': content_id,
            'content_type': content_type,
            'title': title,
            'metadata': metadata or {}
        }
        
        self.current_session['content_shown'].append(record)
        
        # Log to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO session_content_log (
                    session_id, content_id, content_type, title, metadata_json
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                self.current_session['id'],
                content_id,
                content_type,
                title,
                json.dumps(metadata or {})
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Error logging content: {e}")
    
    def record_attention_sample(self, score: float, state: str):
        """Record attention sample during session"""
        if not self.current_session:
            return
        
        self.current_session['attention_scores'].append({
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'state': state
        })
    
    def end_session(self, avg_attention: float, notes: str = "") -> Dict:
        """
        End current session and save summary
        
        Returns session summary and collected data
        """
        if not self.current_session:
            return {'success': False, 'error': 'No active session'}
        
        try:
            elapsed = (datetime.now() - self.current_session['start_time']).total_seconds() / 60
            
            session_data = {
                'block_name': self.current_session['block_name'],
                'block_type': self.current_session['block_type'],
                'duration_minutes': round(elapsed, 1),
                'goal_minutes': self.current_session['goal_duration_minutes'],
                'average_attention': round(avg_attention, 2),
                'content_count': len(self.current_session['content_shown']),
                'content_shown': self.current_session['content_shown'],
                'attention_samples': self.current_session['attention_scores'],
                'notes': notes,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE time_block_sessions
                SET end_time = datetime('now'),
                    actual_duration_minutes = ?,
                    attention_average = ?,
                    content_consumed = ?,
                    session_notes = ?,
                    completed = TRUE
                WHERE id = ?
            """, (
                elapsed,
                avg_attention,
                json.dumps(session_data['content_shown']),
                notes,
                self.current_session['id']
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Session ended: {elapsed:.0f}m, avg attention {avg_attention:.0%}")
            
            result = {
                'success': True,
                'session_data': session_data,
                'message': f"Session complete: {elapsed:.0f}m @ {avg_attention:.0%} attention"
            }
            
            self.current_session = None
            return result
        
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_stats(self) -> Dict:
        """Get current session progress"""
        if not self.current_session:
            return {'active': False}
        
        elapsed = (datetime.now() - self.current_session['start_time']).total_seconds() / 60
        goal = self.current_session['goal_duration_minutes']
        
        avg_attention = (
            sum(s['score'] for s in self.current_session['attention_scores']) / 
            len(self.current_session['attention_scores'])
            if self.current_session['attention_scores'] else 0
        )
        
        return {
            'active': True,
            'block_name': self.current_session['block_name'],
            'elapsed_minutes': round(elapsed, 1),
            'goal_minutes': goal,
            'time_percent': round((elapsed / goal) * 100, 1),
            'average_attention': round(avg_attention, 2),
            'threshold': self.current_session['attentiveness_threshold'],
            'content_count': len(self.current_session['content_shown']),
            'last_updated': datetime.now().isoformat()
        }
