"""
Progress Testing System - Generates quizzes and tracks learning progress
"""

import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ProgressTester:
    """
    Generates tests/quizzes to monitor learning progress
    """
    
    def __init__(self, db_path: Path, config_path: Optional[Path] = None):
        """Initialize progress tester"""
        self.db_path = db_path
        
        if config_path is None:
            config_path = Path.cwd() / "interests.json"
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def generate_quiz(self, topic: str, difficulty: str = 'medium', 
                     num_questions: int = 10) -> Dict:
        """
        Generate a quiz for a specific topic
        
        Args:
            topic: Subject/topic for the quiz
            difficulty: 'easy', 'medium', 'hard'
            num_questions: Number of questions to generate
        
        Returns:
            Dict with quiz metadata and questions
        """
        quiz_id = str(uuid.uuid4())
        
        # Sample quiz structure (in production, use AI to generate)
        quiz = {
            'quiz_id': quiz_id,
            'topic': topic,
            'difficulty': difficulty,
            'num_questions': num_questions,
            'created_at': datetime.now().isoformat(),
            'time_limit_minutes': num_questions * 2,  # 2 minutes per question
            'questions': self._generate_questions(topic, difficulty, num_questions)
        }
        
        # Save quiz to database
        self._save_quiz(quiz)
        
        return quiz
    
    def _generate_questions(self, topic: str, difficulty: str, 
                           num_questions: int) -> List[Dict]:
        """Generate quiz questions (sample implementation)"""
        questions = []
        
        for i in range(num_questions):
            question = {
                'question_id': f"q{i+1}",
                'question_text': f"Question {i+1} about {topic}",
                'type': 'multiple_choice',  # or 'true_false', 'short_answer'
                'options': [
                    {'id': 'a', 'text': 'Option A'},
                    {'id': 'b', 'text': 'Option B'},
                    {'id': 'c', 'text': 'Option C'},
                    {'id': 'd', 'text': 'Option D'}
                ],
                'correct_answer': 'a',
                'explanation': f'Explanation for question {i+1}',
                'points': 10
            }
            questions.append(question)
        
        return questions
    
    def _save_quiz(self, quiz: Dict):
        """Save quiz to database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quizzes (
                    quiz_id TEXT PRIMARY KEY,
                    topic TEXT,
                    difficulty TEXT,
                    num_questions INTEGER,
                    created_at TEXT,
                    quiz_json TEXT
                )
            """)
            
            cursor.execute("""
                INSERT INTO quizzes (quiz_id, topic, difficulty, num_questions, created_at, quiz_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                quiz['quiz_id'],
                quiz['topic'],
                quiz['difficulty'],
                quiz['num_questions'],
                quiz['created_at'],
                json.dumps(quiz)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Quiz {quiz['quiz_id']} saved")
        except Exception as e:
            logger.error(f"Error saving quiz: {e}")
    
    def submit_quiz_answers(self, quiz_id: str, answers: Dict) -> Dict:
        """
        Submit quiz answers and get results
        
        Args:
            quiz_id: Quiz ID
            answers: Dict mapping question_id -> answer
        
        Returns:
            Dict with score, correct/incorrect breakdown, explanations
        """
        try:
            # Load quiz from database
            quiz = self._load_quiz(quiz_id)
            if not quiz:
                return {'error': 'Quiz not found'}
            
            # Grade the quiz
            results = self._grade_quiz(quiz, answers)
            
            # Save results
            self._save_quiz_results(quiz_id, answers, results)
            
            return results
        except Exception as e:
            logger.error(f"Error submitting quiz: {e}")
            return {'error': str(e)}
    
    def _load_quiz(self, quiz_id: str) -> Optional[Dict]:
        """Load quiz from database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT quiz_json FROM quizzes WHERE quiz_id = ?
            """, (quiz_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"Error loading quiz: {e}")
            return None
    
    def _grade_quiz(self, quiz: Dict, answers: Dict) -> Dict:
        """Grade the quiz"""
        total_questions = len(quiz['questions'])
        correct_count = 0
        results_by_question = []
        
        for question in quiz['questions']:
            q_id = question['question_id']
            user_answer = answers.get(q_id)
            correct_answer = question['correct_answer']
            
            is_correct = (user_answer == correct_answer)
            if is_correct:
                correct_count += 1
            
            results_by_question.append({
                'question_id': q_id,
                'question_text': question['question_text'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question['explanation'],
                'points_earned': question['points'] if is_correct else 0,
                'points_possible': question['points']
            })
        
        total_points = sum(q['points'] for q in quiz['questions'])
        earned_points = sum(r['points_earned'] for r in results_by_question)
        
        return {
            'quiz_id': quiz['quiz_id'],
            'topic': quiz['topic'],
            'total_questions': total_questions,
            'correct_count': correct_count,
            'incorrect_count': total_questions - correct_count,
            'score_percentage': (correct_count / total_questions * 100) if total_questions > 0 else 0,
            'points_earned': earned_points,
            'points_possible': total_points,
            'results_by_question': results_by_question,
            'submitted_at': datetime.now().isoformat()
        }
    
    def _save_quiz_results(self, quiz_id: str, answers: Dict, results: Dict):
        """Save quiz results to database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quiz_results (
                    result_id TEXT PRIMARY KEY,
                    quiz_id TEXT,
                    submitted_at TEXT,
                    score_percentage REAL,
                    correct_count INTEGER,
                    total_questions INTEGER,
                    answers_json TEXT,
                    results_json TEXT,
                    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
                )
            """)
            
            result_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO quiz_results 
                (result_id, quiz_id, submitted_at, score_percentage, correct_count, total_questions, answers_json, results_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id,
                quiz_id,
                results['submitted_at'],
                results['score_percentage'],
                results['correct_count'],
                results['total_questions'],
                json.dumps(answers),
                json.dumps(results)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Quiz results saved: {result_id}")
        except Exception as e:
            logger.error(f"Error saving quiz results: {e}")
    
    def get_progress_summary(self, topic: Optional[str] = None) -> Dict:
        """
        Get learning progress summary across all quizzes
        
        Args:
            topic: Optional topic filter
        
        Returns:
            Dict with aggregated progress stats
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if topic:
                cursor.execute("""
                    SELECT qr.*, q.topic
                    FROM quiz_results qr
                    JOIN quizzes q ON qr.quiz_id = q.quiz_id
                    WHERE q.topic = ?
                    ORDER BY qr.submitted_at DESC
                """, (topic,))
            else:
                cursor.execute("""
                    SELECT qr.*, q.topic
                    FROM quiz_results qr
                    JOIN quizzes q ON qr.quiz_id = q.quiz_id
                    ORDER BY qr.submitted_at DESC
                """)
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return {
                    'total_quizzes': 0,
                    'average_score': 0,
                    'topics_covered': [],
                    'recent_quizzes': []
                }
            
            # Calculate stats
            scores = [row[3] for row in rows]  # score_percentage column
            topics = list(set([row[7] for row in rows]))  # topic column
            
            recent_quizzes = []
            for row in rows[:10]:  # Last 10 quizzes
                recent_quizzes.append({
                    'quiz_id': row[1],
                    'topic': row[7],
                    'submitted_at': row[2],
                    'score_percentage': row[3],
                    'correct_count': row[4],
                    'total_questions': row[5]
                })
            
            return {
                'total_quizzes': len(rows),
                'average_score': sum(scores) / len(scores),
                'topics_covered': topics,
                'recent_quizzes': recent_quizzes,
                'highest_score': max(scores),
                'lowest_score': min(scores)
            }
        except Exception as e:
            logger.error(f"Error getting progress summary: {e}")
            return {'error': str(e)}
