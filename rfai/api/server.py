"""
Enhanced RFAI API Server
Extends the existing Learning_AI app with full RFAI features
"""

import os
import sys
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import RFAI components
from rfai.ai.plan_generator import PlanGeneratorAI
from rfai.ai.pace_learner_rl import PaceLearnerRL
from rfai.ai.content_digest_ai import ContentDigestAI
from rfai.ai.srs_engine import AdaptiveSRS
from rfai.ai.schedule_optimizer import ScheduleOptimizer
from rfai.ai.plan_format_processor import PlanFormatProcessor
from database.init_db import get_db_connection, init_database

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask app"""
    app = Flask(__name__)
    CORS(app)
    
    # Configuration
    app.config['RFAI_DATA_DIR'] = Path.home() / ".rfai"
    app.config['RFAI_DB_PATH'] = app.config['RFAI_DATA_DIR'] / "data" / "rfai.db"
    
    # Ensure data directory exists
    app.config['RFAI_DATA_DIR'].mkdir(parents=True, exist_ok=True)
    (app.config['RFAI_DATA_DIR'] / "data").mkdir(parents=True, exist_ok=True)
    
    # Initialize database if needed
    if not app.config['RFAI_DB_PATH'].exists():
        logger.info("Initializing database...")
        init_database(app.config['RFAI_DB_PATH'])
    
    # Initialize AI components
    app.plan_generator = PlanGeneratorAI()
    app.pace_learner = None  # Initialized on demand
    app.content_digester = ContentDigestAI()
    app.srs_engine = None  # Initialized on demand
    app.schedule_optimizer = None  # Initialized on demand
    
    logger.info("RFAI API Server initialized")
    
    # ============================================================================
    # LEARNING PLAN ENDPOINTS
    # ============================================================================
    
    @app.route('/api/plans/generate', methods=['POST'])
    def generate_plan():
        """Generate a new learning plan"""
        try:
            data = request.json
            topic = data.get('topic')
            user_context = data.get('user_context', {})
            
            if not topic:
                return jsonify({'error': 'Topic is required'}), 400
            
            logger.info(f"Generating plan for topic: {topic}")
            
            # Generate plan
            plan = app.plan_generator.generate_plan(topic, user_context)
            
            # Save to database
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO learning_plans (
                    id, topic, estimated_duration_weeks, daily_time_hours,
                    current_week, current_day, status, plan_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan['plan_id'],
                plan['topic'],
                plan['estimated_duration_weeks'],
                plan['daily_time_hours'],
                1,
                1,
                'active',
                json.dumps(plan)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Plan saved: {plan['plan_id']}")
            
            return jsonify({
                'success': True,
                'plan_id': plan['plan_id'],
                'topic': plan['topic'],
                'estimated_weeks': plan['estimated_duration_weeks'],
                'preview': {
                    'week_1_theme': plan['weeks'][0]['theme'] if plan['weeks'] else None,
                    'total_weeks': len(plan['weeks'])
                }
            }), 201
            
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/plans/<plan_id>', methods=['GET'])
    def get_plan(plan_id):
        """Get a specific learning plan"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM learning_plans WHERE id = ?
            """, (plan_id,))
            
            plan_row = cursor.fetchone()
            conn.close()
            
            if not plan_row:
                return jsonify({'error': 'Plan not found'}), 404
            
            plan = dict(plan_row)
            if plan['plan_json']:
                plan['plan_data'] = json.loads(plan['plan_json'])
            
            return jsonify(plan)
            
        except Exception as e:
            logger.error(f"Error getting plan: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/plans', methods=['GET'])
    def list_plans():
        """List all learning plans"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, topic, estimated_duration_weeks, current_week,
                       current_day, status, created_at
                FROM learning_plans
                ORDER BY created_at DESC
            """)
            
            plans = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({'plans': plans})
            
        except Exception as e:
            logger.error(f"Error listing plans: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/plans/<plan_id>/current-day', methods=['GET'])
    def get_current_day(plan_id):
        """Get the current day for a plan"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            # Get plan
            cursor.execute("""
                SELECT plan_json, current_week, current_day 
                FROM learning_plans WHERE id = ?
            """, (plan_id,))
            
            plan_row = cursor.fetchone()
            if not plan_row:
                conn.close()
                return jsonify({'error': 'Plan not found'}), 404
            
            plan_data = json.loads(plan_row['plan_json'])
            current_week = plan_row['current_week']
            current_day = plan_row['current_day']
            
            conn.close()
            
            # Find current day in plan
            if current_week <= len(plan_data['weeks']):
                week = plan_data['weeks'][current_week - 1]
                if current_day <= len(week['days']):
                    day = week['days'][current_day - 1]
                    
                    return jsonify({
                        'plan_id': plan_id,
                        'week': current_week,
                        'day': current_day,
                        'day_data': day,
                        'week_theme': week['theme']
                    })
            
            return jsonify({'error': 'Current day not found in plan'}), 404
            
        except Exception as e:
            logger.error(f"Error getting current day: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/plans/<plan_id>/advance', methods=['POST'])
    def advance_plan(plan_id):
        """Move to next day in plan"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            # Get current position
            cursor.execute("""
                SELECT current_week, current_day, plan_json
                FROM learning_plans WHERE id = ?
            """, (plan_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({'error': 'Plan not found'}), 404
            
            current_week = row['current_week']
            current_day = row['current_day']
            plan_data = json.loads(row['plan_json'])
            
            # Calculate next position
            days_in_week = len(plan_data['weeks'][current_week - 1]['days'])
            
            if current_day < days_in_week:
                # Move to next day in same week
                new_week = current_week
                new_day = current_day + 1
            else:
                # Move to first day of next week
                new_week = current_week + 1
                new_day = 1
            
            # Update plan
            cursor.execute("""
                UPDATE learning_plans
                SET current_week = ?, current_day = ?
                WHERE id = ?
            """, (new_week, new_day, plan_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'week': new_week,
                'day': new_day
            })
            
        except Exception as e:
            logger.error(f"Error advancing plan: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # GOAL ENDPOINTS
    # ============================================================================
    
    @app.route('/api/goals', methods=['GET', 'POST'])
    def handle_goals():
        """List or create goals"""
        if request.method == 'GET':
            try:
                conn = get_db_connection(app.config['RFAI_DB_PATH'])
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM goals WHERE status = 'active'
                    ORDER BY created_at DESC
                """)
                
                goals = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for goal in goals:
                    if goal['subtopics']:
                        goal['subtopics'] = json.loads(goal['subtopics'])
                    if goal['resources']:
                        goal['resources'] = json.loads(goal['resources'])
                
                conn.close()
                
                return jsonify({'goals': goals})
                
            except Exception as e:
                logger.error(f"Error listing goals: {e}")
                return jsonify({'error': str(e)}), 500
        
        else:  # POST
            try:
                data = request.json
                goal_id = str(uuid.uuid4())
                
                conn = get_db_connection(app.config['RFAI_DB_PATH'])
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO goals (
                        id, name, timeline_months, target_hours,
                        subtopics, resources, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    goal_id,
                    data['name'],
                    data.get('timeline_months', 6),
                    data.get('target_hours', 180),
                    json.dumps(data.get('subtopics', [])),
                    json.dumps(data.get('resources', {})),
                    'active'
                ))
                
                conn.commit()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'goal_id': goal_id
                }), 201
                
            except Exception as e:
                logger.error(f"Error creating goal: {e}")
                return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # ACTIVITY & FOCUS ENDPOINTS
    # ============================================================================
    
    @app.route('/api/activity/today', methods=['GET'])
    def get_today_activity():
        """Get today's activity logs"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            cursor.execute("""
                SELECT * FROM time_logs
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            """, (today,))
            
            logs = [dict(row) for row in cursor.fetchall()]
            
            # Get focus states
            cursor.execute("""
                SELECT * FROM focus_states
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            """, (today,))
            
            focus_states = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            # Calculate summary
            total_time = sum(log.get('duration_seconds', 0) for log in logs)
            focus_time = sum(
                log.get('duration_seconds', 0) 
                for log in logs 
                if log.get('focus_state') == 'FOCUSED'
            )
            
            return jsonify({
                'date': str(today),
                'total_time_seconds': total_time,
                'focus_time_seconds': focus_time,
                'focus_percentage': (focus_time / total_time * 100) if total_time > 0 else 0,
                'logs': logs[:50],  # Return last 50
                'focus_states': focus_states[:50]
            })
            
        except Exception as e:
            logger.error(f"Error getting today's activity: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/focus/current', methods=['GET'])
    def get_current_focus():
        """Get current focus state"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM focus_states
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            state = cursor.fetchone()
            conn.close()
            
            if state:
                state_dict = dict(state)
                if state_dict.get('signal_breakdown'):
                    state_dict['signal_breakdown'] = json.loads(state_dict['signal_breakdown'])
                return jsonify(state_dict)
            else:
                return jsonify({
                    'state': 'UNKNOWN',
                    'confidence': 0.0,
                    'message': 'No focus data available yet'
                })
            
        except Exception as e:
            logger.error(f"Error getting current focus: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # SRS (SPACED REPETITION) ENDPOINTS
    # ============================================================================
    
    @app.route('/api/srs/due-cards', methods=['GET'])
    def get_due_cards():
        """Get flashcards due for review"""
        try:
            max_cards = request.args.get('max', 20, type=int)
            
            if app.srs_engine is None:
                app.srs_engine = AdaptiveSRS(str(app.config['RFAI_DB_PATH']))
            
            cards = app.srs_engine.get_due_cards(max_cards=max_cards)
            
            return jsonify({
                'cards': cards,
                'count': len(cards)
            })
            
        except Exception as e:
            logger.error(f"Error getting due cards: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/srs/review', methods=['POST'])
    def review_card():
        """Submit a card review"""
        try:
            data = request.json
            card_id = data.get('card_id')
            quality = data.get('quality')  # 0-5
            
            if app.srs_engine is None:
                app.srs_engine = AdaptiveSRS(str(app.config['RFAI_DB_PATH']))
            
            result = app.srs_engine.review_card(card_id, quality)
            
            return jsonify({
                'success': True,
                'next_review': result.get('next_review_date')
            })
            
        except Exception as e:
            logger.error(f"Error reviewing card: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # PACE LEARNING (RL) ENDPOINTS
    # ============================================================================
    
    @app.route('/api/rl/weekly-adjustment', methods=['POST'])
    def weekly_adjustment():
        """Run weekly pace adjustment"""
        try:
            if app.pace_learner is None:
                app.pace_learner = PaceLearnerRL(str(app.config['RFAI_DB_PATH']))
            
            adjustment = app.pace_learner.weekly_adjustment()
            
            return jsonify({
                'success': True,
                'action': adjustment['action'],
                'changes': adjustment.get('changes', {}),
                'reward': adjustment.get('reward', 0)
            })
            
        except Exception as e:
            logger.error(f"Error running weekly adjustment: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # SYSTEM STATUS ENDPOINTS
    # ============================================================================
    
    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Get system status"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            # Get daemon status
            cursor.execute("SELECT * FROM daemon_status")
            daemons = [dict(row) for row in cursor.fetchall()]
            
            # Get config
            cursor.execute("SELECT * FROM system_config")
            config = {row['key']: row['value'] for row in cursor.fetchall()}
            
            # Get counts
            cursor.execute("SELECT COUNT(*) as count FROM learning_plans")
            plan_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM goals")
            goal_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM flashcards")
            card_count = cursor.fetchone()['count']
            
            conn.close()
            
            return jsonify({
                'system': 'RFAI',
                'version': config.get('system_version', '1.0.0'),
                'daemons': daemons,
                'stats': {
                    'plans': plan_count,
                    'goals': goal_count,
                    'flashcards': card_count
                },
                'config': config
            })
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # HEALTH CHECK
    # ============================================================================
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    
    return app


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server"""
    app = create_app()
    logger.info(f"Starting RFAI API Server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_server(debug=True)
