"""
Enhanced RFAI API Server
Extends the existing Learning_AI app with full RFAI features
"""

import sys
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import RFAI components
from rfai.ai.plan_generator import PlanGeneratorAI
from rfai.ai.pace_learner_rl import PaceLearnerRL
from rfai.ai.content_digest_ai import ContentDigestAI
from rfai.ai.srs_engine import AdaptiveSRS
from rfai.ai.schedule_optimizer import ScheduleOptimizerAI
from rfai.ai.time_block_content import TimeBlockContentManager
from rfai.ai.block_access_manager import BlockAccessManager
from rfai.ai.session_manager import SessionManager
from rfai.ai.data_collector import DataCollector
from database.init_db import get_db_connection, init_database

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask app"""
    # Load and normalize .env so integrations can read API keys
    try:
        from rfai.config.env import load_env
        load_env(override=False)
    except Exception:
        # Never fail app startup because of dotenv parsing
        pass

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
    app.content_scheduler = None  # Initialized on demand
    app.time_block_manager = TimeBlockContentManager()  # Time-block aware content
    app.session_manager = SessionManager(app.config['RFAI_DB_PATH'])  # Session tracking
    app.data_collector = DataCollector(app.config['RFAI_DB_PATH'])  # Data collection for AI
    
    # Initialize content fetcher for real recommendations
    from rfai.ai.content_fetcher import ContentFetcher
    app.content_fetcher = ContentFetcher()
    logger.info("Content fetcher initialized")
    
    # Initialize progress tester for quizzes
    from rfai.ai.progress_tester import ProgressTester
    app.progress_tester = ProgressTester(app.config['RFAI_DB_PATH'])
    logger.info("Progress tester initialized")
    
    logger.info("RFAI API Server initialized")

    @app.route('/', methods=['GET'])
    def home():
        """Serve the RFAI dashboard"""
        try:
            # Try enhanced dashboard first
            enhanced_path = Path(__file__).parent.parent / 'ui' / 'static' / 'dashboard_enhanced.html'
            if enhanced_path.exists():
                return enhanced_path.read_text(encoding='utf-8')
            
            # Fallback to original dashboard
            dashboard_path = Path(__file__).parent.parent / 'ui' / 'static' / 'index.html'
            if dashboard_path.exists():
                return dashboard_path.read_text(encoding='utf-8')
            else:
                # Fallback if dashboard file doesn't exist
                return (
                    "<h2>RFAI Server</h2>"
                    "<ul>"
                    "<li><a href='/health'>/health</a></li>"
                    "<li><a href='/api/status'>/api/status</a></li>"
                    "<li><a href='/api/plans'>/api/plans</a></li>"
                    "<li><a href='/api/schedule/daily'>/api/schedule/daily</a></li>"
                    "</ul>",
                    200,
                    {'Content-Type': 'text/html; charset=utf-8'},
                )
        except Exception as e:
            logger.error(f"Error serving dashboard: {e}")
            return jsonify({'error': 'Dashboard unavailable'}), 500
    
    @app.route('/dashboard', methods=['GET'])
    def dashboard_enhanced():
        """Serve the enhanced 3-hour plan dashboard"""
        try:
            dashboard_path = Path(__file__).parent.parent / 'ui' / 'static' / 'dashboard_enhanced.html'
            if dashboard_path.exists():
                return dashboard_path.read_text(encoding='utf-8')
            else:
                return jsonify({'error': 'Enhanced dashboard not found'}), 404
        except Exception as e:
            logger.error(f"Error serving enhanced dashboard: {e}")
            return jsonify({'error': 'Dashboard unavailable'}), 500
    
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
            try:
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
            finally:
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
    # TIMETABLE & SCHEDULE ENDPOINTS
    # ============================================================================
    
    @app.route('/api/timetable/today', methods=['GET'])
    def get_today_timetable():
        """Get today's timetable slots"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, start_time, end_time, task, subtask, context,
                       min_focus_target, recommended_content_type, completed
                FROM timetable_slots
                WHERE day = 'weekday' OR day = 'all'
                ORDER BY start_time ASC
                LIMIT 10
            """)
            
            slots = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({
                'slots': slots,
                'count': len(slots)
            })
            
        except Exception as e:
            logger.error(f"Error getting timetable: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/discovery/search', methods=['POST'])
    def discover_content():
        """Search for content by topic"""
        try:
            data = request.json
            topic = data.get('topic', 'machine learning')
            
            try:
                from rfai.ai.multi_source_discovery import MultiSourceDiscovery
                discovery = MultiSourceDiscovery()
                results = discovery.discover(topic, max_results=10)
                
                return jsonify({
                    'topic': topic,
                    'results': results,
                    'count': len(results)
                })
            except Exception as e:
                logger.warning(f"Discovery failed: {e}")
                return jsonify({
                    'topic': topic,
                    'results': [],
                    'note': 'Add API keys to .env: YOUTUBE_API_KEY, PERPLEXITY_API_KEY, OMDB_API_KEY',
                    'count': 0
                })
            
        except Exception as e:
            logger.error(f"Error discovering content: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # CONTENT SCHEDULER ENDPOINTS (3-HOUR DAILY PLAN)
    # ============================================================================
    
    @app.route('/api/schedule/daily', methods=['GET'])
    def get_daily_schedule():
        """Get today's content schedule (3-hour plan)"""
        try:
            if app.content_scheduler is None:
                from rfai.ai.content_scheduler import ContentScheduler
                app.content_scheduler = ContentScheduler()
            
            schedule = app.content_scheduler.generate_daily_schedule()
            
            return jsonify({
                'success': True,
                'schedule': schedule,
                'summary': app.content_scheduler.get_schedule_summary(schedule)
            })
            
        except Exception as e:
            logger.error(f"Error getting daily schedule: {e}")
            return jsonify({
                'error': str(e),
                'note': 'Ensure interests.json and daily_3hr_plan.md are configured'
            }), 500
    
    @app.route('/api/content/rate', methods=['POST'])
    def rate_content():
        """Rate a piece of content"""
        try:
            data = request.json
            content_id = data.get('content_id')
            rating = data.get('rating')  # 1-5
            tags = data.get('tags', [])
            time_spent = data.get('time_spent_seconds', 0)
            
            if not content_id or not rating:
                return jsonify({'error': 'content_id and rating required'}), 400
            
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            rating_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO ratings (
                    id, content_id, rating, tags, time_spent_seconds, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rating_id,
                content_id,
                rating,
                json.dumps(tags),
                time_spent,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'rating_id': rating_id,
                'message': 'Rating saved successfully'
            })
            
        except Exception as e:
            logger.error(f"Error rating content: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/movie/post-review', methods=['POST'])
    def submit_movie_review():
        """Submit post-movie review"""
        try:
            data = request.json
            movie_id = data.get('movie_id')
            answers = data.get('answers', {})
            
            if not movie_id:
                return jsonify({'error': 'movie_id required'}), 400
            
            # Store review as a special rating with review data
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            rating_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO ratings (
                    id, content_id, rating, tags, context, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rating_id,
                movie_id,
                5,  # Assumed completion rating
                json.dumps(['movie_review', 'post_viewing']),
                json.dumps({'review_answers': answers}),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'review_id': rating_id,
                'message': 'Movie review submitted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error submitting movie review: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stats/daily', methods=['GET'])
    def get_daily_stats():
        """Get daily statistics for dashboard"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            # Get time logs
            cursor.execute("""
                SELECT focus_state, SUM(duration_seconds) as total_seconds
                FROM time_logs
                WHERE DATE(timestamp) = ?
                GROUP BY focus_state
            """, (today,))
            
            focus_breakdown = {row['focus_state']: row['total_seconds'] for row in cursor.fetchall()}
            
            # Get learning plan progress
            cursor.execute("""
                SELECT daily_time_hours, current_week, current_day
                FROM learning_plans
                WHERE status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            plan_row = cursor.fetchone()
            target_hours = plan_row['daily_time_hours'] if plan_row else 3.0
            current_week = plan_row['current_week'] if plan_row else 1
            current_day = plan_row['current_day'] if plan_row else 1
            
            # Calculate actual hours today
            total_seconds = sum(focus_breakdown.values())
            actual_hours = total_seconds / 3600.0
            
            # Get content ratings today
            cursor.execute("""
                SELECT content_id, rating
                FROM ratings
                WHERE DATE(timestamp) = ?
            """, (today,))
            
            ratings_today = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return jsonify({
                'date': str(today),
                'learning_plan': {
                    'target_hours': target_hours,
                    'actual_hours': round(actual_hours, 2),
                    'completion_percent': round((actual_hours / target_hours) * 100, 1) if target_hours > 0 else 0,
                    'current_week': current_week,
                    'current_day': current_day
                },
                'focus_breakdown': focus_breakdown,
                'ratings_count': len(ratings_today),
                'time_allocation': {
                    'youtube': round(focus_breakdown.get('YOUTUBE', 0) / 3600, 2),
                    'papers': round(focus_breakdown.get('PAPERS', 0) / 3600, 2),
                    'movies': round(focus_breakdown.get('MOVIES', 0) / 3600, 2)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # TIME-BLOCK CONTENT ENDPOINTS
    # ============================================================================
    
    @app.route('/api/schedule/current-block', methods=['GET'])
    def get_current_block():
        """Get current active time block and content recommendations"""
        try:
            block_info = app.time_block_manager.get_block_info()
            
            if block_info.get('active'):
                # Get context-specific content
                result = {
                    'block': block_info,
                    'theme': app.time_block_manager.get_theme(),
                    'progress': app.time_block_manager.get_progress_goal()
                }
                
                # Add content recommendations based on block type
                block_type = block_info.get('content_type')
                
                if 'science' in block_type:
                    result['content'] = {
                        'youtube': app.time_block_manager.get_youtube_content(),
                        'papers': app.time_block_manager.get_papers_content()
                    }
                elif 'self_help' in block_type:
                    result['content'] = {
                        'youtube': app.time_block_manager.get_youtube_content()
                    }
                elif 'movie' in block_type:
                    result['content'] = {
                        'movies': app.time_block_manager.get_movie_content()
                    }
                
                return jsonify(result)
            else:
                return jsonify(block_info), 200
            
        except Exception as e:
            logger.error(f"Error getting current block: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedule/full-day', methods=['GET'])
    def get_full_schedule():
        """Get complete daily schedule with all time blocks"""
        try:
            schedule = app.time_block_manager.get_full_schedule()
            return jsonify(schedule)
        except Exception as e:
            logger.error(f"Error getting full schedule: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedule/override', methods=['POST'])
    def set_manual_override():
        """Manually override current time block"""
        try:
            data = request.json
            block_name = data.get('block_name')  # None to clear override
            
            app.time_block_manager.set_manual_override(block_name)
            
            # Refresh current block
            app.time_block_manager.current_block = app.time_block_manager._get_current_block()
            
            return jsonify({
                'override_active': app.time_block_manager.manual_override_block is not None,
                'current_block': app.time_block_manager.current_block.get('name') if app.time_block_manager.current_block else None,
                'message': f"Override set to '{block_name}'" if block_name else "Override cleared"
            })
        except Exception as e:
            logger.error(f"Error setting override: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedule/override', methods=['DELETE'])
    def clear_manual_override():
        """Clear manual override and return to automatic time detection"""
        try:
            app.time_block_manager.clear_override()
            return jsonify({
                'override_active': False,
                'message': 'Manual override cleared'
            })
        except Exception as e:
            logger.error(f"Error clearing override: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedule/available-blocks', methods=['GET'])
    def get_available_blocks():
        """Get list of all available time blocks for override"""
        try:
            schedule = app.time_block_manager.config.get('daily_schedule', {}).get('time_blocks', [])
            blocks = [
                {
                    'name': block.get('name'),
                    'content_type': block.get('content_type'),
                    'icon': block.get('icon'),
                    'duration_hours': block.get('duration_hours')
                }
                for block in schedule
            ]
            return jsonify({'blocks': blocks})
        except Exception as e:
            logger.error(f"Error getting available blocks: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/content/youtube-recommendations', methods=['GET'])
    def get_youtube_recommendations():
        """Get YouTube video recommendations"""
        try:
            # Get recommendations from time block manager (includes all blocks)
            content = app.time_block_manager.get_youtube_content()
            
            # If it's not from a specific block, fetch actual videos
            if 'All Blocks' in content.get('block', '') or not app.time_block_manager.current_block:
                videos = app.content_fetcher.fetch_science_youtube(max_results=5)
                videos.extend(app.content_fetcher.fetch_self_help_youtube(max_results=5))
                
                return jsonify({
                    'videos': videos,
                    'count': len(videos),
                    'source': 'youtube'
                })
            
            # Otherwise try to fetch actual videos for this block
            videos = []
            block_type = content.get('type', '')
            if 'science' in block_type.lower():
                videos = app.content_fetcher.fetch_science_youtube(max_results=10)
            elif 'self_help' in block_type.lower():
                videos = app.content_fetcher.fetch_self_help_youtube(max_results=10)
            else:
                videos = app.content_fetcher.fetch_science_youtube(max_results=5)
                videos.extend(app.content_fetcher.fetch_self_help_youtube(max_results=5))
            
            return jsonify({
                'videos': videos,
                'count': len(videos),
                'source': 'youtube',
                'block': content.get('block')
            })
        except Exception as e:
            logger.error(f"Error getting YouTube recommendations: {e}")
            return jsonify({'error': str(e)}), 500
    @app.route('/api/content/movie-recommendations', methods=['GET'])
    def get_movie_recommendations():
        """Get movie recommendations for cinema block"""
        try:
            # Try to fetch actual movie data
            movies = app.content_fetcher.fetch_movies(max_results=10)
            
            # If no movies from fetcher, get from content manager
            if not movies:
                content = app.time_block_manager.get_movie_content()
                return jsonify(content)
            
            return jsonify({
                'movies': movies,
                'count': len(movies),
                'source': 'imdb'
            })
        except Exception as e:
            logger.error(f"Error getting movie recommendations: {e}")
            # Fallback to sample data
            return jsonify({
                'movies': app.content_fetcher._get_sample_movies_curated(),
                'count': 10,
                'source': 'sample'
            })
    
    @app.route('/api/content/paper-recommendations', methods=['GET'])
    def get_paper_recommendations():
        """Get research paper recommendations"""
        try:
            # Fetch papers from ArXiv (or get sample papers as fallback)
            papers = app.content_fetcher.fetch_research_papers(max_results=10)
            
            # Also get the metadata from time block manager
            metadata = app.time_block_manager.get_papers_content()
            
            return jsonify({
                'papers': papers,
                'research_papers': papers,
                'count': len(papers),
                'source': 'arxiv',
                'metadata': metadata
            })
        except Exception as e:
            logger.error(f"Error getting paper recommendations: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # ATTENTION MONITORING ENDPOINTS
    # ============================================================================
    
    @app.route('/api/attention/current', methods=['GET'])
    def get_current_attention():
        """Get current attention score and state"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            # Get latest attention log
            cursor.execute("""
                SELECT session_id, timestamp, state, score, confidence,
                       trend, signals_json, capabilities_json
                FROM attention_log
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return jsonify({
                    'session_id': row['session_id'],
                    'timestamp': row['timestamp'],
                    'state': row['state'],
                    'score': row['score'],
                    'confidence': row['confidence'],
                    'trend': row['trend'],
                    'signals': json.loads(row['signals_json']),
                    'capabilities': json.loads(row['capabilities_json'])
                })
            else:
                return jsonify({'error': 'No attention data available'}), 404
        
        except Exception as e:
            logger.error(f"Error getting attention: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/attention/history', methods=['GET'])
    def get_attention_history():
        """Get attention history for session or time range"""
        try:
            limit = request.args.get('limit', 100, type=int)
            session_id = request.args.get('session_id')
            
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            if session_id:
                cursor.execute("""
                    SELECT timestamp, state, score, confidence, trend
                    FROM attention_log
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (session_id, limit))
            else:
                cursor.execute("""
                    SELECT timestamp, state, score, confidence, trend
                    FROM attention_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # Calculate statistics
            if records:
                scores = [r['score'] for r in records]
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
                
                state_counts = {}
                for r in records:
                    state_counts[r['state']] = state_counts.get(r['state'], 0) + 1
                
                return jsonify({
                    'records': records,
                    'statistics': {
                        'average_score': round(avg_score, 2),
                        'max_score': max_score,
                        'min_score': min_score,
                        'state_distribution': state_counts,
                        'total_samples': len(records)
                    }
                })
            else:
                return jsonify({'error': 'No attention history available'}), 404
        
        except Exception as e:
            logger.error(f"Error getting attention history: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/time-blocks/session/start', methods=['POST'])
    def start_time_block_session():
        """Start tracking a time block session"""
        try:
            data = request.json
            block_name = data.get('block_name')
            block_type = data.get('block_type')
            goal_duration_minutes = data.get('goal_duration_minutes', 60)
            
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO time_block_sessions (
                    block_name, block_type, start_time, goal_duration_minutes
                ) VALUES (?, ?, datetime('now'), ?)
            """, (block_name, block_type, goal_duration_minutes))
            
            conn.commit()
            session_id = cursor.lastrowid
            conn.close()
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'message': f'Started {block_name} session'
            }), 201
        
        except Exception as e:
            logger.error(f"Error starting block session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/time-blocks/session/<session_id>/end', methods=['POST'])
    def end_time_block_session(session_id):
        """End a time block session and record summary"""
        try:
            data = request.json or {}
            notes = data.get('notes', '')
            content_consumed = data.get('content_consumed', {})
            
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            # Get attention average for this session
            cursor.execute("""
                SELECT AVG(score) as avg_score
                FROM attention_log
                WHERE timestamp >= (
                    SELECT start_time FROM time_block_sessions WHERE id = ?
                )
            """, (session_id,))
            
            result = cursor.fetchone()
            avg_attention = result['avg_score'] if result else None
            
            # Update session
            cursor.execute("""
                UPDATE time_block_sessions
                SET end_time = datetime('now'),
                    actual_duration_minutes = 
                        (julianday('now') - julianday(start_time)) * 24 * 60,
                    attention_average = ?,
                    content_consumed = ?,
                    session_notes = ?,
                    completed = TRUE
                WHERE id = ?
            """, (avg_attention, json.dumps(content_consumed), notes, session_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Session ended',
                'attention_average': avg_attention
            })
        
        except Exception as e:
            logger.error(f"Error ending block session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/session/current', methods=['GET'])
    def get_current_session():
        """Get current active session status"""
        try:
            session = app.session_manager.get_current_session()
            
            if session:
                stats = app.session_manager.get_session_stats()
                return jsonify({
                    'active': True,
                    'block_name': session['block_name'],
                    'block_type': session['block_type'],
                    'stats': stats
                })
            else:
                return jsonify({'active': False, 'message': 'No active session'}), 200
        
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/session/start', methods=['POST'])
    def start_session():
        """Start a new learning block session"""
        try:
            data = request.json or {}
            block_name = data.get('block_name')
            block_type = data.get('block_type')
            goal_minutes = data.get('goal_minutes', 60)
            threshold = data.get('attentiveness_threshold', 0.7)
            
            result = app.session_manager.start_session(
                block_name, block_type, goal_minutes, threshold
            )
            
            return jsonify(result), 201 if result['success'] else 400
        
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/session/end', methods=['POST'])
    def end_session():
        """End current session"""
        try:
            data = request.json or {}
            avg_attention = data.get('avg_attention', 0)
            notes = data.get('notes', '')
            
            result = app.session_manager.end_session(avg_attention, notes)
            
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/data/training-dataset', methods=['GET'])
    def get_training_dataset():
        """Get aggregated data for AI model training"""
        try:
            days = request.args.get('days', 7, type=int)
            dataset = app.data_collector.get_training_dataset(days)
            
            return jsonify(dataset)
        
        except Exception as e:
            logger.error(f"Error getting training dataset: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/data/export', methods=['POST'])
    def export_training_data():
        """Export training data for external ML use"""
        try:
            result = app.data_collector.export_training_data()
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/user-patterns', methods=['GET'])
    def get_user_patterns():
        """Get analyzed user behavior patterns"""
        try:
            patterns = app.data_collector.analyze_user_patterns()
            return jsonify(patterns)
        
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # TIME-BLOCK ACCESS CONTROL (SOFT-LOCK SYSTEM)
    # ============================================================================
    
    @app.route('/api/access/status', methods=['GET'])
    def get_access_status():
        """Get current lock status and allowed content types"""
        try:
            status = app.access_manager.get_access_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Access status error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/access/check/<content_type>', methods=['GET'])
    def check_content_access(content_type):
        """Check if specific content type can be accessed"""
        try:
            can_access = app.access_manager.can_access_content(content_type)
            status = app.access_manager.get_access_status()
            return jsonify({
                'content_type': content_type,
                'can_access': can_access,
                'lock_status': status
            })
        except Exception as e:
            logger.error(f"Access check error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/activity/log', methods=['POST'])
    def log_activity():
        """Log user activity during time-block session"""
        try:
            data = request.get_json()
            session_id = data.get('session_id')
            action = data.get('action')
            content_type = data.get('content_type')
            page_title = data.get('page_title', '')
            
            if not session_id or not action:
                return jsonify({'error': 'session_id and action required'}), 400
            
            app.access_manager.log_activity(session_id, action, content_type, page_title)
            return jsonify({'status': 'logged'})
        except Exception as e:
            logger.error(f"Activity log error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/block/progress/<session_id>', methods=['GET'])
    def get_block_progress(session_id):
        """Get progress toward time-block completion goal"""
        try:
            progress = app.access_manager.get_block_progress(session_id)
            return jsonify(progress)
        except Exception as e:
            logger.error(f"Progress error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/page-activity', methods=['GET'])
    def get_page_activity():
        """Get page/URL activity history from current session"""
        try:
            limit = request.args.get('limit', 50, type=int)
            db = sqlite3.connect(DB_PATH)
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, app_name, window_title, page_title, page_info_json, duration_seconds
                FROM time_logs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            logs = [dict(row) for row in cursor.fetchall()]
            db.close()
            
            return jsonify({'page_activity': logs, 'count': len(logs)})
        except Exception as e:
            logger.error(f"Page activity error: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # TIME-BLOCK ACCESS CONTROL (SOFT-LOCK SYSTEM)
    # ============================================================================
    
    @app.route('/api/access-control/check', methods=['GET'])
    def check_access():
        """Check if current content access is allowed (soft-lock)"""
        try:
            requested_content_type = request.args.get('content_type')  # youtube|papers|movies
            
            # Get current active block
            current_block = app.time_block_manager.get_block_info()
            
            if not current_block.get('active'):
                # No active block = full access to everything
                return jsonify({
                    'access_allowed': True,
                    'reason': 'No active time block - unrestricted access',
                    'lock_active': False,
                    'current_block': None
                })
            
            # Active block detected - check if requested content matches block type
            active_content_type = current_block.get('content_type')
            
            # Map content type requests to block types
            content_to_block_map = {
                'science_youtube': 'science_youtube_and_papers',
                'science_papers': 'science_youtube_and_papers',
                'self_help_youtube': 'self_help_youtube',
                'movies': 'artistic_movies'
            }
            
            block_type_for_content = content_to_block_map.get(requested_content_type, requested_content_type)
            
            if block_type_for_content == active_content_type:
                # Requested content matches current block
                return jsonify({
                    'access_allowed': True,
                    'reason': f'Accessing allowed content for {current_block["name"]}',
                    'lock_active': True,
                    'current_block': current_block,
                    'attention_required': current_block.get('attentiveness_threshold', 0.7)
                })
            else:
                # Requested content does NOT match current block
                return jsonify({
                    'access_allowed': False,
                    'reason': f'Content locked during {current_block["name"]} block',
                    'lock_active': True,
                    'current_block': current_block,
                    'allowed_content': active_content_type,
                    'requested_content': requested_content_type
                }), 403
        
        except Exception as e:
            logger.error(f"Error checking access: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/activity/log-page', methods=['POST'])
    def log_page_activity_post():
        """Log current app/page activity with focus state"""
        try:
            data = request.json
            app_name = data.get('app_name')
            page_title = data.get('page_title')
            page_info = data.get('page_info', {})
            focus_state = data.get('focus_state', 'ACTIVE')
            
            # Log the activity
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            log_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO time_logs (
                    id, timestamp, actual_app, page_title, 
                    page_info_json, focus_state, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                datetime.now(),
                app_name,
                page_title,
                json.dumps(page_info),
                focus_state,
                1
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'logged': True,
                'log_id': log_id
            }), 201
        
        except Exception as e:
            logger.error(f"Error logging page activity: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/activity/block-activity', methods=['POST'])
    def log_block_activity():
        """Log activity during active time block session"""
        try:
            data = request.json
            session_id = data.get('session_id')
            action = data.get('action')
            content_type = data.get('content_type')
            page_title = data.get('page_title')
            attention_score = data.get('attention_score')
            
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO block_activity_log (
                    session_id, timestamp, action, content_type, 
                    page_title, attention_score
                ) VALUES (?, datetime('now'), ?, ?, ?, ?)
            """, (session_id, action, content_type, page_title, attention_score))
            
            if action == 'content_view':
                content_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO session_content_log (
                        session_id, content_id, content_type, title, metadata_json
                    ) VALUES (?, ?, ?, ?, ?)
                """, (session_id, content_id, content_type, page_title, 
                      json.dumps({'timestamp': datetime.now().isoformat()})))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'logged': True,
                'session_id': session_id,
                'action': action
            }), 201
        
        except Exception as e:
            logger.error(f"Error logging block activity: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/session-activity/<session_id>', methods=['GET'])
    def get_session_activity(session_id):
        """Get all activity logged during a session"""
        try:
            conn = get_db_connection(app.config['RFAI_DB_PATH'])
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, action, content_type, page_title, attention_score
                FROM block_activity_log
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            
            activities = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT content_id, content_type, title, metadata_json
                FROM session_content_log
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,))
            
            content_consumed = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return jsonify({
                'session_id': session_id,
                'activities': activities,
                'content_consumed': content_consumed,
                'total_activities': len(activities),
                'total_content_items': len(content_consumed)
            })
        
        except Exception as e:
            logger.error(f"Error getting session activity: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # REAL CONTENT FETCHING (YouTube, Papers, Movies, Study Plans)
    # ============================================================================
    
    @app.route('/api/fetch/youtube/science', methods=['GET'])
    def fetch_science_videos():
        """Fetch actual science YouTube videos"""
        try:
            max_results = int(request.args.get('max_results', 10))
            videos = app.content_fetcher.fetch_science_youtube(max_results=max_results)
            return jsonify({
                'videos': videos,
                'count': len(videos),
                'source': 'youtube_api' if videos and 'sample' not in videos[0].get('id', '') else 'sample_data'
            })
        except Exception as e:
            logger.error(f"Error fetching science videos: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/fetch/youtube/selfhelp', methods=['GET'])
    def fetch_selfhelp_videos():
        """Fetch actual self-help YouTube videos"""
        try:
            max_results = int(request.args.get('max_results', 10))
            videos = app.content_fetcher.fetch_self_help_youtube(max_results=max_results)
            return jsonify({
                'videos': videos,
                'count': len(videos),
                'source': 'youtube_api' if videos and 'selfhelp' not in videos[0].get('id', '') else 'sample_data'
            })
        except Exception as e:
            logger.error(f"Error fetching self-help videos: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/fetch/papers', methods=['GET'])
    def fetch_papers():
        """Fetch actual research papers from ArXiv"""
        try:
            max_results = int(request.args.get('max_results', 10))
            papers = app.content_fetcher.fetch_research_papers(max_results=max_results)
            return jsonify({
                'papers': papers,
                'count': len(papers),
                'source': 'arxiv_api' if papers else 'sample_data'
            })
        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/fetch/movies', methods=['GET'])
    def fetch_movies():
        """Fetch movie recommendations"""
        try:
            max_results = int(request.args.get('max_results', 10))
            movies = app.content_fetcher.fetch_movies(max_results=max_results)
            return jsonify({
                'movies': movies,
                'count': len(movies),
                'source': 'imdb_api' if movies else 'sample_data'
            })
        except Exception as e:
            logger.error(f"Error fetching movies: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/fetch/study-plan-content', methods=['POST'])
    def fetch_study_plan_content():
        """Get content recommendations based on study plan using Perplexity"""
        try:
            data = request.json
            study_plan = data.get('study_plan', '')
            
            if not study_plan:
                return jsonify({'error': 'study_plan required'}), 400
            
            recommendations = app.content_fetcher.get_study_plan_content(study_plan)
            return jsonify(recommendations)
        except Exception as e:
            logger.error(f"Error generating study plan content: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/fetch/current-block-content', methods=['GET'])
    def fetch_current_block_content():
        """Fetch actual content for current active time block"""
        try:
            block_info = app.time_block_manager.get_block_info()
            
            if not block_info.get('active'):
                return jsonify({
                    'active': False,
                    'message': 'No active time block',
                    'content': []
                })
            
            content_type = block_info.get('content_type')
            content = []
            
            if content_type == 'science_youtube_and_papers':
                # Fetch both YouTube videos and papers
                videos = app.content_fetcher.fetch_science_youtube(max_results=5)
                papers = app.content_fetcher.fetch_research_papers(max_results=5)
                content = {
                    'youtube_videos': videos,
                    'research_papers': papers
                }
            elif content_type == 'self_help_youtube':
                videos = app.content_fetcher.fetch_self_help_youtube(max_results=10)
                content = {
                    'youtube_videos': videos
                }
            elif content_type == 'artistic_movies':
                movies = app.content_fetcher.fetch_movies(max_results=10)
                content = {
                    'movies': movies
                }
            
            return jsonify({
                'active': True,
                'block': block_info,
                'content': content
            })
        except Exception as e:
            logger.error(f"Error fetching current block content: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================================
    # QUIZ & PROGRESS TESTING
    # ============================================================================
    
    @app.route('/api/quiz/generate', methods=['POST'])
    def generate_quiz():
        """Generate a quiz for a topic"""
        try:
            data = request.json
            topic = data.get('topic')
            difficulty = data.get('difficulty', 'medium')
            num_questions = data.get('num_questions', 10)
            
            if not topic:
                return jsonify({'error': 'topic required'}), 400
            
            quiz = app.progress_tester.generate_quiz(
                topic=topic,
                difficulty=difficulty,
                num_questions=num_questions
            )
            
            return jsonify(quiz)
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/quiz/<quiz_id>', methods=['GET'])
    def get_quiz(quiz_id):
        """Get quiz by ID"""
        try:
            quiz = app.progress_tester._load_quiz(quiz_id)
            if not quiz:
                return jsonify({'error': 'Quiz not found'}), 404
            return jsonify(quiz)
        except Exception as e:
            logger.error(f"Error loading quiz: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/quiz/<quiz_id>/submit', methods=['POST'])
    def submit_quiz(quiz_id):
        """Submit quiz answers and get results"""
        try:
            data = request.json
            answers = data.get('answers', {})
            
            results = app.progress_tester.submit_quiz_answers(quiz_id, answers)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error submitting quiz: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/progress/summary', methods=['GET'])
    def get_progress_summary():
        """Get learning progress summary"""
        try:
            topic = request.args.get('topic')
            summary = app.progress_tester.get_progress_summary(topic=topic)
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Error getting progress summary: {e}")
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
