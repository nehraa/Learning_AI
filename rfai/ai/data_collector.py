"""
Data Collection & AI Training Pipeline
Collects user behavior, attention patterns, content performance for ML
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import sqlite3

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Collects user data for AI training:
    - Content performance (engagement, completion rate)
    - Attention patterns (peak hours, triggers)
    - User preferences (implicit from behavior)
    - Learning effectiveness (quiz performance vs attention)
    """
    
    def __init__(self, db_path: Path = None):
        if db_path is None:
            data_dir = Path.home() / ".rfai" / "data"
            db_path = data_dir / "rfai.db"
        
        self.db_path = db_path
    
    def collect_session_data(self, session_id: int) -> Dict:
        """
        Extract comprehensive data from a completed session
        for AI training
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get session
            cursor.execute("""
                SELECT * FROM time_block_sessions WHERE id = ?
            """, (session_id,))
            session = dict(cursor.fetchone() or {})
            
            # Get content shown
            cursor.execute("""
                SELECT * FROM session_content_log WHERE session_id = ?
                ORDER BY timestamp
            """, (session_id,))
            content_log = [dict(row) for row in cursor.fetchall()]
            
            # Get attention data during session
            cursor.execute("""
                SELECT timestamp, state, score, confidence
                FROM attention_log
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            """, (session['start_time'], session['end_time'] or datetime.now()))
            attention_data = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            # Aggregate metrics
            if attention_data:
                attention_scores = [a['score'] for a in attention_data]
                avg_attention = sum(attention_scores) / len(attention_scores)
                max_attention = max(attention_scores)
                min_attention = min(attention_scores)
            else:
                avg_attention = session.get('attention_average', 0)
                max_attention = avg_attention
                min_attention = avg_attention
            
            # Categorize attention
            focused_time = sum(1 for a in attention_data if a['state'] == 'FOCUSED')
            distracted_time = sum(1 for a in attention_data if a['state'] == 'DISTRACTED')
            
            return {
                'session_id': session_id,
                'block_type': session.get('block_type'),
                'block_name': session.get('block_name'),
                'duration_minutes': session.get('actual_duration_minutes', 0),
                'goal_minutes': session.get('goal_duration_minutes', 0),
                'completed': session.get('completed', False),
                'metrics': {
                    'avg_attention': round(avg_attention, 2),
                    'max_attention': round(max_attention, 2),
                    'min_attention': round(min_attention, 2),
                    'focused_samples': focused_time,
                    'distracted_samples': distracted_time,
                    'total_samples': len(attention_data)
                },
                'content': {
                    'items_shown': len(content_log),
                    'items': content_log
                },
                'metadata': {
                    'date': session.get('start_time', '')[:10],
                    'time_of_day': self._extract_hour(session.get('start_time', '')),
                    'day_of_week': self._get_day_of_week(session.get('start_time', ''))
                }
            }
        
        except Exception as e:
            logger.error(f"Error collecting session data: {e}")
            return {}
    
    def get_training_dataset(self, days: int = 7) -> Dict:
        """
        Get aggregated training data for last N days
        
        Returns:
            Dataset ready for ML model training
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get completed sessions
            cursor.execute("""
                SELECT id FROM time_block_sessions
                WHERE completed = TRUE AND start_time > ?
                ORDER BY start_time DESC
            """, (cutoff_date,))
            
            session_ids = [row['id'] for row in cursor.fetchall()]
            conn.close()
            
            # Collect data from each session
            sessions_data = []
            for sid in session_ids:
                data = self.collect_session_data(sid)
                if data:
                    sessions_data.append(data)
            
            # Aggregate by block type
            by_block_type = {}
            for session in sessions_data:
                block = session['block_type']
                if block not in by_block_type:
                    by_block_type[block] = []
                by_block_type[block].append(session)
            
            # Calculate statistics
            stats = {}
            for block_type, sessions in by_block_type.items():
                attentions = [s['metrics']['avg_attention'] for s in sessions]
                completions = sum(1 for s in sessions if s['completed']) / len(sessions)
                
                stats[block_type] = {
                    'sessions': len(sessions),
                    'avg_attention': round(sum(attentions) / len(attentions), 2) if attentions else 0,
                    'completion_rate': round(completions, 2),
                    'total_content_items': sum(s['content']['items_shown'] for s in sessions)
                }
            
            return {
                'period_days': days,
                'total_sessions': len(sessions_data),
                'statistics': stats,
                'sessions': sessions_data,
                'ready_for_training': len(sessions_data) >= 5  # Need min 5 sessions
            }
        
        except Exception as e:
            logger.error(f"Error getting training dataset: {e}")
            return {}
    
    def export_training_data(self, output_path: Path = None) -> Dict:
        """
        Export training data in standard format for ML
        
        Format: JSON with nested structure for easy pandas/TensorFlow loading
        """
        if output_path is None:
            output_path = Path.home() / ".rfai" / "training_data.json"
        
        try:
            dataset = self.get_training_dataset(days=30)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(dataset, f, indent=2, default=str)
            
            logger.info(f"✅ Training data exported to {output_path}")
            
            return {
                'success': True,
                'path': str(output_path),
                'size': len(dataset.get('sessions', [])),
                'ready': dataset.get('ready_for_training', False)
            }
        
        except Exception as e:
            logger.error(f"Error exporting training data: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze_user_patterns(self) -> Dict:
        """
        Analyze user behavior patterns for personalization
        
        Returns:
        - Peak focus hours
        - Best performing content types
        - Optimal session duration
        - Content recommendations
        """
        try:
            dataset = self.get_training_dataset(days=30)
            sessions = dataset.get('sessions', [])
            
            if not sessions:
                return {'error': 'Insufficient data'}
            
            # Hour analysis
            hours = {}
            for session in sessions:
                hour = session['metadata'].get('time_of_day', '00')
                if hour not in hours:
                    hours[hour] = []
                hours[hour].append(session['metrics']['avg_attention'])
            
            peak_hours = sorted(
                [(h, sum(attn)/len(attn)) for h, attn in hours.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            # Block type analysis
            by_type = {}
            for session in sessions:
                block = session['block_type']
                if block not in by_type:
                    by_type[block] = {'attention': [], 'completion': []}
                by_type[block]['attention'].append(session['metrics']['avg_attention'])
                by_type[block]['completion'].append(1 if session['completed'] else 0)
            
            block_stats = {}
            for block, data in by_type.items():
                block_stats[block] = {
                    'avg_attention': round(sum(data['attention']) / len(data['attention']), 2),
                    'completion_rate': round(sum(data['completion']) / len(data['completion']), 2)
                }
            
            return {
                'peak_focus_hours': [f"{h}:00-{h}:59" for h, _ in peak_hours],
                'peak_attention_scores': [round(score, 2) for _, score in peak_hours],
                'best_block_type': max(block_stats.items(), key=lambda x: x[1]['completion_rate'])[0],
                'block_performance': block_stats,
                'total_sessions_analyzed': len(sessions)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {'error': str(e)}
    
    def _extract_hour(self, timestamp: str) -> str:
        """Extract hour from ISO timestamp"""
        try:
            return timestamp.split('T')[1].split(':')[0]
        except:
            return '00'
    
    def _get_day_of_week(self, timestamp: str) -> str:
        """Get day of week from ISO timestamp"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            return days[dt.weekday()]
        except:
            return 'Unknown'
