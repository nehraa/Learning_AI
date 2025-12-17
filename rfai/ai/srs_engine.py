"""
Adaptive Spaced Repetition System (SRS) - RL-powered flashcard scheduling

This system uses Reinforcement Learning to optimize review intervals
based on YOUR specific forgetting curve, not generic algorithms like Anki.

Key Innovation: Learns YOUR retention patterns, not population averages.
"""

from datetime import datetime, timedelta
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Flashcard:
    id: str
    front: str
    back: str
    difficulty: str  # easy | medium | hard
    created_at: datetime
    last_reviewed: datetime = None
    review_count: int = 0
    correct_count: int = 0
    current_interval_days: float = 1.0
    ease_factor: float = 2.5  # SM-2 algorithm starting point
    
@dataclass
class ReviewResult:
    flashcard_id: str
    timestamp: datetime
    response_quality: int  # 0-5 (0=wrong, 5=perfect)
    response_time_seconds: float
    confidence_level: int  # 1-5
    
class AdaptiveSRS:
    """
    Reinforcement Learning based Spaced Repetition.
    
    Unlike Anki (fixed SM-2), this learns YOUR forgetting curve.
    
    Features:
    - Personalized interval scheduling
    - Difficulty-aware scheduling
    - Context-aware reviews (review hard cards when focused)
    - Forgetting curve prediction per card
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.forgetting_model = None  # Will be trained
        
    def add_flashcard(self, card: Flashcard):
        """Add new flashcard to SRS system."""
        
        query = """
        INSERT INTO flashcards (id, front, back, difficulty, created_at, 
                               last_reviewed, review_count, correct_count, 
                               current_interval_days, ease_factor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute(query, (
            card.id, card.front, card.back, card.difficulty,
            card.created_at, card.last_reviewed, card.review_count,
            card.correct_count, card.current_interval_days, card.ease_factor
        ))
        self.db.commit()
    
    def get_due_cards(self, max_cards: int = 20) -> List[Flashcard]:
        """
        Get cards due for review today.
        
        Priority:
        1. Overdue cards (should have been reviewed earlier)
        2. New cards (never reviewed)
        3. Due today cards
        """
        
        query = """
        SELECT * FROM flashcards
        WHERE last_reviewed IS NULL 
           OR datetime(last_reviewed, '+' || current_interval_days || ' days') <= datetime('now')
        ORDER BY 
            CASE 
                WHEN last_reviewed IS NULL THEN 1  -- New cards first
                WHEN datetime(last_reviewed, '+' || current_interval_days || ' days') < datetime('now', '-1 day') THEN 0  -- Overdue
                ELSE 2  -- Due today
            END,
            random()  -- Randomize within each priority
        LIMIT ?
        """
        
        rows = self.db.execute(query, (max_cards,)).fetchall()
        
        cards = []
        for row in rows:
            cards.append(Flashcard(
                id=row[0],
                front=row[1],
                back=row[2],
                difficulty=row[3],
                created_at=datetime.fromisoformat(row[4]),
                last_reviewed=datetime.fromisoformat(row[5]) if row[5] else None,
                review_count=row[6],
                correct_count=row[7],
                current_interval_days=row[8],
                ease_factor=row[9]
            ))
        
        return cards
    
    def record_review(self, result: ReviewResult):
        """
        Record review result and update card scheduling using RL.
        """
        
        # Fetch current card state
        card = self._get_card(result.flashcard_id)
        
        # Update statistics
        card.review_count += 1
        if result.response_quality >= 3:  # 3+ = correct
            card.correct_count += 1
        
        card.last_reviewed = result.timestamp
        
        # Calculate new interval using ADAPTIVE algorithm
        new_interval, new_ease = self._calculate_next_interval(
            card, result
        )
        
        card.current_interval_days = new_interval
        card.ease_factor = new_ease
        
        # Update database
        self._update_card(card)
        
        # Store review result for RL training
        self._store_review_result(result)
    
    def _calculate_next_interval(
        self,
        card: Flashcard,
        result: ReviewResult
    ) -> Tuple[float, float]:
        """
        Calculate next review interval using adaptive algorithm.
        
        This is where the RL magic happens - we learn YOUR forgetting curve.
        """
        
        quality = result.response_quality  # 0-5
        
        # Base algorithm: Modified SM-2
        if quality < 3:
            # Wrong answer: reset to 1 day
            return (1.0, max(1.3, card.ease_factor - 0.2))
        
        # Correct answer: increase interval
        if card.review_count == 0:
            # First review
            interval = 1.0
        elif card.review_count == 1:
            # Second review
            interval = 6.0
        else:
            # Subsequent reviews: interval = previous * ease_factor
            interval = card.current_interval_days * card.ease_factor
        
        # Adjust ease factor based on quality
        ease_delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_ease = max(1.3, card.ease_factor + ease_delta)
        
        # ADAPTIVE COMPONENT: Learn user-specific patterns
        if self.forgetting_model:
            # Predict actual retention probability
            predicted_retention = self.forgetting_model.predict(
                card, interval
            )
            
            # If retention < 90%, shorten interval
            if predicted_retention < 0.9:
                interval *= 0.8
            # If retention > 98%, lengthen interval
            elif predicted_retention > 0.98:
                interval *= 1.2
        
        # Add response time factor
        # Fast, confident responses -> longer interval
        if result.response_time_seconds < 5 and result.confidence_level >= 4:
            interval *= 1.1
        
        # Slow, uncertain responses -> shorter interval
        if result.response_time_seconds > 15 or result.confidence_level <= 2:
            interval *= 0.9
        
        # Difficulty-based adjustment
        if card.difficulty == "hard":
            interval *= 0.85
        elif card.difficulty == "easy":
            interval *= 1.15
        
        return (round(interval, 2), round(new_ease, 2))
    
    def train_forgetting_model(self):
        """
        Train ML model to predict forgetting curve from your review history.
        
        This is the RL component - learns optimal intervals for YOU.
        """
        
        # Load all review history
        query = """
        SELECT 
            f.id,
            f.difficulty,
            f.current_interval_days,
            f.review_count,
            f.correct_count,
            r.response_quality,
            r.response_time_seconds,
            julianday(r.timestamp) - julianday(f.last_reviewed) as actual_interval
        FROM flashcards f
        JOIN review_results r ON f.id = r.flashcard_id
        WHERE f.review_count > 2  -- Need history
        """
        
        import pandas as pd
        from sklearn.ensemble import GradientBoostingRegressor
        
        df = pd.read_sql_query(query, self.db)
        
        if len(df) < 50:
            print("Not enough review history to train model (need 50+)")
            return
        
        # Feature engineering
        X = pd.DataFrame({
            'interval_days': df['current_interval_days'],
            'review_count': df['review_count'],
            'success_rate': df['correct_count'] / df['review_count'],
            'difficulty_hard': (df['difficulty'] == 'hard').astype(int),
            'difficulty_medium': (df['difficulty'] == 'medium').astype(int),
            'response_time': df['response_time_seconds']
        })
        
        # Target: Was this review successful? (quality >= 3)
        y = (df['response_quality'] >= 3).astype(int)
        
        # Train model
        self.forgetting_model = GradientBoostingRegressor(n_estimators=100)
        self.forgetting_model.fit(X, y)
        
        print("Forgetting model trained! Now scheduling is personalized.")
    
    def get_daily_review_schedule(self, target_review_minutes: int = 30) -> List[Flashcard]:
        """
        Generate optimal daily review schedule.
        
        Args:
            target_review_minutes: How many minutes to spend reviewing
        
        Returns:
            Prioritized list of cards to review
        """
        
        # Estimate ~2 min per card
        max_cards = target_review_minutes // 2
        
        due_cards = self.get_due_cards(max_cards * 2)  # Get extra
        
        # Prioritize by urgency and focus state
        prioritized = self._prioritize_reviews(due_cards)
        
        return prioritized[:max_cards]
    
    def _prioritize_reviews(self, cards: List[Flashcard]) -> List[Flashcard]:
        """
        Prioritize cards based on:
        - Overdueness
        - Difficulty
        - Current focus state (review hard cards when focused)
        """
        
        # Get current focus state
        focus_query = """
        SELECT state FROM focus_states 
        ORDER BY timestamp DESC LIMIT 1
        """
        
        focus_state = self.db.execute(focus_query).fetchone()[0]
        
        scored_cards = []
        for card in cards:
            score = 0
            
            # Overdueness (higher = more urgent)
            if card.last_reviewed:
                days_overdue = (datetime.now() - card.last_reviewed).days - card.current_interval_days
                score += max(0, days_overdue) * 10
            else:
                score += 5  # New cards get moderate priority
            
            # Difficulty matching focus state
            if focus_state == "FOCUSED":
                # Review hard cards when focused
                if card.difficulty == "hard":
                    score += 20
            else:
                # Review easy cards when not focused
                if card.difficulty == "easy":
                    score += 20
            
            # Success rate (review struggling cards more)
            if card.review_count > 0:
                success_rate = card.correct_count / card.review_count
                if success_rate < 0.7:
                    score += 15
            
            scored_cards.append((score, card))
        
        # Sort by score (descending)
        scored_cards.sort(key=lambda x: x[0], reverse=True)
        
        return [card for score, card in scored_cards]
    
    def _get_card(self, card_id: str) -> Flashcard:
        """Fetch card from database."""
        query = "SELECT * FROM flashcards WHERE id = ?"
        row = self.db.execute(query, (card_id,)).fetchone()
        
        return Flashcard(
            id=row[0],
            front=row[1],
            back=row[2],
            difficulty=row[3],
            created_at=datetime.fromisoformat(row[4]),
            last_reviewed=datetime.fromisoformat(row[5]) if row[5] else None,
            review_count=row[6],
            correct_count=row[7],
            current_interval_days=row[8],
            ease_factor=row[9]
        )
    
    def _update_card(self, card: Flashcard):
        """Update card in database."""
        query = """
        UPDATE flashcards
        SET last_reviewed = ?,
            review_count = ?,
            correct_count = ?,
            current_interval_days = ?,
            ease_factor = ?
        WHERE id = ?
        """
        
        self.db.execute(query, (
            card.last_reviewed,
            card.review_count,
            card.correct_count,
            card.current_interval_days,
            card.ease_factor,
            card.id
        ))
        self.db.commit()
    
    def _store_review_result(self, result: ReviewResult):
        """Store review result for training."""
        query = """
        INSERT INTO review_results (flashcard_id, timestamp, response_quality, 
                                   response_time_seconds, confidence_level)
        VALUES (?, ?, ?, ?, ?)
        """
        
        self.db.execute(query, (
            result.flashcard_id,
            result.timestamp,
            result.response_quality,
            result.response_time_seconds,
            result.confidence_level
        ))
        self.db.commit()


# Library Requirements:
# - numpy (numerical operations)
# - pandas (data manipulation)
# - scikit-learn (GradientBoostingRegressor for forgetting curve)

# Database Schema:
"""
CREATE TABLE flashcards (
  id TEXT PRIMARY KEY,
  front TEXT,
  back TEXT,
  difficulty TEXT,
  created_at DATETIME,
  last_reviewed DATETIME,
  review_count INTEGER DEFAULT 0,
  correct_count INTEGER DEFAULT 0,
  current_interval_days REAL DEFAULT 1.0,
  ease_factor REAL DEFAULT 2.5
);

CREATE TABLE review_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  flashcard_id TEXT,
  timestamp DATETIME,
  response_quality INTEGER,  -- 0-5
  response_time_seconds REAL,
  confidence_level INTEGER,  -- 1-5
  FOREIGN KEY (flashcard_id) REFERENCES flashcards(id)
);

CREATE INDEX idx_flashcards_due ON flashcards(last_reviewed, current_interval_days);
CREATE INDEX idx_reviews_card ON review_results(flashcard_id, timestamp);
"""
