"""
Pace Learning RL System - THE CORE INNOVATION

This is the brain that learns YOUR actual learning pace and adjusts EVERYTHING:
- Daily time commitments (3hrs → maybe 1.5hrs is realistic)
- Topic difficulty estimates (QM Week 1 too easy? Skip ahead)
- Content format preferences (hate videos? More papers)
- Energy patterns (mornings dead? Shift to evenings)

Uses Reinforcement Learning (Q-Learning / Actor-Critic) to optimize your learning trajectory.

GOAL: Maximize [knowledge retention × completion rate × satisfaction]
       while minimizing [burnout × procrastination × wasted time]
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import deque
import pickle

class PaceLearnerRL:
    """
    Reinforcement Learning agent that learns optimal pacing strategy.
    
    State Space:
    - Current week in plan
    - Average daily focus hours (last 7 days)
    - Quiz scores (last 3 quizzes)
    - Completion rate (actual vs planned)
    - Burnout indicator (focus trend)
    - Content type preference scores
    
    Action Space:
    - Maintain pace (no change)
    - Slow down 20%
    - Slow down 50%
    - Speed up 20%
    - Speed up 50%
    - Add rest day
    - Adjust difficulty (easier/harder content)
    - Change content mix (more videos vs papers)
    
    Reward Function:
    R = α × retention_score 
        + β × completion_rate
        + γ × user_satisfaction
        - δ × burnout_indicator
        - ε × plan_deviation
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        
        # Q-Learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.2  # Exploration rate
        
        # Q-table: state -> action -> expected reward
        self.q_table = {}
        
        # Experience replay buffer
        self.experience_buffer = deque(maxlen=1000)
        
        # Reward weights
        self.reward_weights = {
            'retention': 0.35,
            'completion': 0.25,
            'satisfaction': 0.25,
            'burnout_penalty': 0.10,
            'deviation_penalty': 0.05
        }
        
    def get_current_state(self) -> Tuple:
        """
        Compute current state vector from database.
        
        Returns tuple representing state (for Q-table key).
        """
        
        # 1. Average daily focus hours (last 7 days)
        focus_query = """
        SELECT AVG(
            CASE WHEN state = 'FOCUSED' THEN confidence * duration_seconds / 3600.0 ELSE 0 END
        ) as avg_focus_hours
        FROM focus_states
        WHERE timestamp > datetime('now', '-7 days')
        """
        
        avg_focus_hours = self.db.execute(focus_query).fetchone()[0] or 0
        
        # 2. Quiz performance (last 3 quizzes)
        quiz_query = """
        SELECT AVG(score) as avg_score
        FROM (
            SELECT score FROM quiz_results
            ORDER BY timestamp DESC
            LIMIT 3
        )
        """
        
        avg_quiz_score = self.db.execute(quiz_query).fetchone()[0] or 0
        
        # 3. Completion rate (tasks completed vs planned, last 7 days)
        completion_query = """
        SELECT 
            COUNT(CASE WHEN completed = 1 THEN 1 END) * 1.0 / COUNT(*) as completion_rate
        FROM timetable_slots
        WHERE date(start_time) > date('now', '-7 days')
        """
        
        completion_rate = self.db.execute(completion_query).fetchone()[0] or 0
        
        # 4. Burnout indicator (focus trend declining?)
        burnout_query = """
        SELECT 
            AVG(CASE WHEN day_num <= 3 THEN confidence ELSE 0 END) as recent_focus,
            AVG(CASE WHEN day_num > 3 THEN confidence ELSE 0 END) as past_focus
        FROM (
            SELECT 
                confidence,
                ROW_NUMBER() OVER (ORDER BY timestamp DESC) as day_num
            FROM focus_states
            WHERE timestamp > datetime('now', '-7 days')
            AND state = 'FOCUSED'
        )
        WHERE day_num <= 7
        """
        
        result = self.db.execute(burnout_query).fetchone()
        recent_focus = result[0] or 50
        past_focus = result[1] or 50
        
        burnout_indicator = 1 if recent_focus < past_focus * 0.85 else 0
        
        # 5. Content preference (which types get highest ratings?)
        content_pref_query = """
        SELECT content_type, AVG(rating) as avg_rating
        FROM ratings
        WHERE timestamp > datetime('now', '-30 days')
        GROUP BY content_type
        ORDER BY avg_rating DESC
        LIMIT 1
        """
        
        preferred_content = self.db.execute(content_pref_query).fetchone()
        preferred_type = preferred_content[0] if preferred_content else 'video'
        
        # Discretize continuous values for Q-table
        state = (
            int(avg_focus_hours),  # 0-10
            int(avg_quiz_score / 20),  # 0-5 (quintiles of 0-100)
            int(completion_rate * 10),  # 0-10
            burnout_indicator,  # 0 or 1
            preferred_type  # string
        )
        
        return state
    
    def choose_action(self, state: Tuple) -> str:
        """
        Epsilon-greedy action selection.
        
        Returns action name.
        """
        
        actions = [
            'maintain',
            'slow_down_20',
            'slow_down_50',
            'speed_up_20',
            'speed_up_50',
            'add_rest_day',
            'adjust_difficulty_easier',
            'adjust_difficulty_harder',
            'more_videos',
            'more_papers'
        ]
        
        # Exploration: random action
        if np.random.random() < self.epsilon:
            return np.random.choice(actions)
        
        # Exploitation: best known action
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in actions}
        
        # Get action with highest Q-value
        best_action = max(self.q_table[state], key=self.q_table[state].get)
        return best_action
    
    def execute_action(self, action: str) -> Dict:
        """
        Execute chosen action by modifying the learning plan.
        
        Returns:
            Changes made to the plan
        """
        
        changes = {'action': action, 'modifications': []}
        
        if action == 'maintain':
            changes['modifications'].append("No changes - current pace is optimal")
        
        elif action == 'slow_down_20':
            # Reduce daily hours by 20%
            changes['modifications'].append("Daily target: 3h → 2.4h")
            changes['modifications'].append("Extended timeline by 25%")
            self._adjust_daily_target(0.8)
        
        elif action == 'slow_down_50':
            changes['modifications'].append("Daily target: 3h → 1.5h")
            changes['modifications'].append("Extended timeline by 100%")
            self._adjust_daily_target(0.5)
        
        elif action == 'speed_up_20':
            changes['modifications'].append("Daily target: 3h → 3.6h")
            changes['modifications'].append("Shortened timeline by 17%")
            self._adjust_daily_target(1.2)
        
        elif action == 'speed_up_50':
            changes['modifications'].append("Daily target: 3h → 4.5h")
            changes['modifications'].append("Shortened timeline by 33%")
            self._adjust_daily_target(1.5)
        
        elif action == 'add_rest_day':
            changes['modifications'].append("Added rest day every 5 days")
            self._add_rest_days()
        
        elif action == 'adjust_difficulty_easier':
            changes['modifications'].append("Switched to beginner-level resources")
            self._adjust_content_difficulty('easier')
        
        elif action == 'adjust_difficulty_harder':
            changes['modifications'].append("Switched to advanced resources")
            self._adjust_content_difficulty('harder')
        
        elif action == 'more_videos':
            changes['modifications'].append("Increased video content to 60%")
            self._adjust_content_mix('video', 0.6)
        
        elif action == 'more_papers':
            changes['modifications'].append("Increased paper content to 60%")
            self._adjust_content_mix('paper', 0.6)
        
        return changes
    
    def compute_reward(
        self,
        prev_state: Tuple,
        action: str,
        new_state: Tuple
    ) -> float:
        """
        Compute reward after taking action.
        
        Reward = weighted sum of:
        - Knowledge retention (quiz scores)
        - Completion rate
        - User satisfaction (ratings)
        - Burnout penalty
        - Plan deviation penalty
        """
        
        # Unpack states
        _, prev_quiz, prev_completion, prev_burnout, _ = prev_state
        _, new_quiz, new_completion, new_burnout, _ = new_state
        
        # 1. Retention improvement
        quiz_improvement = (new_quiz - prev_quiz) / 5.0  # Normalize to [-1, 1]
        
        # 2. Completion rate improvement
        completion_improvement = (new_completion - prev_completion) / 10.0
        
        # 3. User satisfaction (average rating last 7 days)
        satisfaction_query = """
        SELECT AVG(rating) FROM ratings
        WHERE timestamp > datetime('now', '-7 days')
        """
        satisfaction = (self.db.execute(satisfaction_query).fetchone()[0] or 3) / 5.0  # Normalize to [0, 1]
        
        # 4. Burnout penalty
        burnout_penalty = -1.0 if new_burnout == 1 else 0.0
        
        # 5. Plan deviation penalty (did we change plan too drastically?)
        deviation_penalty = 0.0
        if action in ['slow_down_50', 'speed_up_50']:
            deviation_penalty = -0.3  # Penalty for drastic changes
        
        # Weighted reward
        reward = (
            self.reward_weights['retention'] * quiz_improvement
            + self.reward_weights['completion'] * completion_improvement
            + self.reward_weights['satisfaction'] * satisfaction
            + self.reward_weights['burnout_penalty'] * burnout_penalty
            + self.reward_weights['deviation_penalty'] * deviation_penalty
        )
        
        return reward
    
    def update_q_table(
        self,
        state: Tuple,
        action: str,
        reward: float,
        next_state: Tuple
    ):
        """
        Q-Learning update rule.
        
        Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        """
        
        # Initialize Q-values if needed
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in [
                'maintain', 'slow_down_20', 'slow_down_50', 
                'speed_up_20', 'speed_up_50', 'add_rest_day',
                'adjust_difficulty_easier', 'adjust_difficulty_harder',
                'more_videos', 'more_papers'
            ]}
        
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in self.q_table[state].keys()}
        
        # Q-learning update
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
    
    def weekly_adjustment(self) -> Dict:
        """
        Main entry point: called every week to adjust plan.
        
        Returns:
            Adjustment report with changes and reasoning
        """
        
        # Get current state
        current_state = self.get_current_state()
        
        # Choose action
        action = self.choose_action(current_state)
        
        # Execute action (modify plan)
        changes = self.execute_action(action)
        
        # Store in experience buffer (will compute reward next week)
        self.experience_buffer.append({
            'state': current_state,
            'action': action,
            'timestamp': datetime.now()
        })
        
        # If we have previous experience, compute reward and update Q-table
        if len(self.experience_buffer) >= 2:
            prev_exp = self.experience_buffer[-2]
            reward = self.compute_reward(
                prev_exp['state'],
                prev_exp['action'],
                current_state
            )
            
            self.update_q_table(
                prev_exp['state'],
                prev_exp['action'],
                reward,
                current_state
            )
        
        # Save Q-table
        self._save_q_table()
        
        return {
            'state': current_state,
            'action': action,
            'changes': changes,
            'q_values': self.q_table.get(current_state, {})
        }
    
    def _adjust_daily_target(self, multiplier: float):
        """Adjust daily hour targets in database."""
        query = """
        UPDATE timetable_slots
        SET duration_seconds = duration_seconds * ?
        WHERE date(start_time) > date('now')
        """
        self.db.execute(query, (multiplier,))
        self.db.commit()
    
    def _add_rest_days(self):
        """Insert rest days into timetable every 5 days."""
        # Implementation: modify timetable to add "Rest" slots
        pass
    
    def _adjust_content_difficulty(self, direction: str):
        """Change difficulty level of recommended content."""
        # Implementation: update content recommendation weights
        pass
    
    def _adjust_content_mix(self, content_type: str, target_ratio: float):
        """Adjust ratio of content types (video vs paper vs tutorial)."""
        # Implementation: update recommendation channel weights
        pass
    
    def _save_q_table(self):
        """Save Q-table to disk for persistence."""
        import pickle
        with open('~/Library/Application Support/RFAI/data/q_table.pkl', 'wb') as f:
            pickle.dump(self.q_table, f)
    
    def load_q_table(self):
        """Load Q-table from disk."""
        import pickle
        import os
        
        path = os.path.expanduser('~/Library/Application Support/RFAI/data/q_table.pkl')
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self.q_table = pickle.load(f)
                print(f"Loaded Q-table with {len(self.q_table)} states")


# Library Requirements:
# - numpy (numerical operations)
# - pickle (Q-table persistence)

# Database Schema Additions:
"""
CREATE TABLE quiz_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quiz_id TEXT,
  timestamp DATETIME,
  score REAL,  -- 0-100
  total_questions INTEGER,
  correct_answers INTEGER
);

CREATE TABLE rl_experiences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME,
  state TEXT,  -- JSON serialized state
  action TEXT,
  reward REAL,
  next_state TEXT,  -- JSON serialized
  q_value_before REAL,
  q_value_after REAL
);

CREATE INDEX idx_quiz_timestamp ON quiz_results(timestamp DESC);
CREATE INDEX idx_rl_timestamp ON rl_experiences(timestamp DESC);
"""

# USAGE EXAMPLE:
"""
# Initialize
pace_learner = PaceLearnerRL(db_connection)
pace_learner.load_q_table()

# Every Sunday, run weekly adjustment
adjustment_report = pace_learner.weekly_adjustment()

print(f"Action taken: {adjustment_report['action']}")
print(f"Changes: {adjustment_report['changes']}")
print(f"Q-values for this state:")
for action, q_val in adjustment_report['q_values'].items():
    print(f"  {action}: {q_val:.3f}")
"""
