"""
Intelligent Schedule Optimizer - ML-powered optimal time slot finder
"""

import numpy as np
from datetime import time, datetime, timedelta
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd

class ScheduleOptimizerAI:
    """
    Uses machine learning to predict optimal scheduling times based on:
    - Historical focus quality by hour
    - Day of week patterns
    - Topic difficulty
    - Energy levels (inferred from focus data)
    - Context (after meals, weather, sleep quality if available)
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def train_model(self):
        """
        Train ML model on historical focus data.
        """
        
        # Load training data
        df = self._load_training_data()
        
        if len(df) < 50:  # Need minimum data
            print("Not enough data to train. Need 50+ focus sessions.")
            return False
        
        # Feature engineering
        X = self._engineer_features(df)
        y = df['focus_quality']  # Target: 0-100 focus score
        
        # Train model
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        
        self.is_trained = True
        return True
    
    def _load_training_data(self) -> pd.DataFrame:
        """
        Load historical focus data with context.
        """
        
        query = """
        SELECT 
            f.timestamp,
            CAST(strftime('%H', f.timestamp) AS INTEGER) as hour,
            CAST(strftime('%w', f.timestamp) AS INTEGER) as day_of_week,
            CAST(strftime('%d', f.timestamp) AS INTEGER) as day_of_month,
            f.state,
            f.confidence as focus_quality,
            t.task,
            t.subtask,
            t.goal_id,
            -- Contextual features
            (SELECT AVG(confidence) 
             FROM focus_states 
             WHERE timestamp BETWEEN datetime(f.timestamp, '-1 hour') 
             AND f.timestamp) as prev_hour_focus,
            
            (SELECT COUNT(*) 
             FROM time_logs 
             WHERE timestamp BETWEEN datetime(f.timestamp, '-1 hour') 
             AND f.timestamp 
             AND focus_state = 'DISTRACTED') as prev_hour_distractions
             
        FROM focus_states f
        LEFT JOIN timetable_slots t ON f.timestamp BETWEEN t.start_time AND t.end_time
        WHERE f.state = 'FOCUSED'
        AND f.timestamp > datetime('now', '-90 days')
        ORDER BY f.timestamp
        """
        
        return pd.read_sql_query(query, self.db)
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create ML features from raw data.
        """
        
        features = pd.DataFrame()
        
        # Temporal features
        features['hour'] = df['hour']
        features['day_of_week'] = df['day_of_week']
        features['is_morning'] = (df['hour'] >= 6) & (df['hour'] < 12)
        features['is_afternoon'] = (df['hour'] >= 12) & (df['hour'] < 18)
        features['is_evening'] = (df['hour'] >= 18) & (df['hour'] < 24)
        features['is_weekend'] = df['day_of_week'].isin([0, 6])  # Sun, Sat
        
        # Contextual features
        features['prev_hour_focus'] = df['prev_hour_focus'].fillna(50)
        features['prev_hour_distractions'] = df['prev_hour_distractions'].fillna(0)
        
        # Cyclical encoding (hour as sine/cosine for ML)
        features['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        features['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Task difficulty (inferred from goal_id)
        # TODO: Add task difficulty scoring
        
        return features
    
    def predict_optimal_slots(
        self,
        task: str,
        duration_hours: float,
        num_days_ahead: int = 7
    ) -> List[Dict]:
        """
        Predict best time slots for a given task over next N days.
        
        Returns:
            List of {date, time, predicted_focus_score} sorted by score
        """
        
        if not self.is_trained:
            self.train_model()
        
        predictions = []
        
        # Generate candidate slots (every hour for next N days)
        for day_offset in range(num_days_ahead):
            date = datetime.now() + timedelta(days=day_offset)
            
            for hour in range(24):
                # Skip sleep hours
                if hour < 6 or hour > 23:
                    continue
                
                # Create feature vector for this slot
                features = self._create_feature_vector(date, hour)
                
                # Predict focus quality
                X_scaled = self.scaler.transform([features])
                predicted_focus = self.model.predict(X_scaled)[0]
                
                predictions.append({
                    'date': date.date(),
                    'time': time(hour, 0),
                    'predicted_focus': predicted_focus,
                    'slot': f"{hour:02d}:00-{hour+1:02d}:00"
                })
        
        # Sort by predicted focus (descending)
        predictions.sort(key=lambda x: x['predicted_focus'], reverse=True)
        
        return predictions[:10]  # Top 10 slots
    
    def _create_feature_vector(self, date: datetime, hour: int) -> List[float]:
        """
        Create feature vector for prediction.
        """
        
        day_of_week = date.weekday()
        
        # Historical average at this hour
        query = f"""
        SELECT AVG(confidence) as avg_focus
        FROM focus_states
        WHERE CAST(strftime('%H', timestamp) AS INTEGER) = {hour}
        AND state = 'FOCUSED'
        """
        
        result = self.db.execute(query).fetchone()
        prev_hour_focus = result[0] if result[0] else 50
        
        return [
            hour,
            day_of_week,
            1 if 6 <= hour < 12 else 0,  # morning
            1 if 12 <= hour < 18 else 0,  # afternoon
            1 if 18 <= hour < 24 else 0,  # evening
            1 if day_of_week in [5, 6] else 0,  # weekend
            prev_hour_focus,
            0,  # prev_hour_distractions (default)
            np.sin(2 * np.pi * hour / 24),  # hour_sin
            np.cos(2 * np.pi * hour / 24)   # hour_cos
        ]
    
    def suggest_reschedule(
        self,
        current_timetable: List[Dict],
        optimization_goal: str = "maximize_focus"
    ) -> Dict:
        """
        Suggest optimal timetable adjustments.
        
        Args:
            current_timetable: Current schedule
            optimization_goal: "maximize_focus" | "minimize_distractions" | "balance_energy"
        
        Returns:
            Suggested timetable changes with reasoning
        """
        
        suggestions = []
        
        for slot in current_timetable:
            task = slot['task']
            current_hour = int(slot['start_time'].split(':')[0])
            
            # Find better slot
            optimal_slots = self.predict_optimal_slots(task, duration_hours=1)
            
            best_slot = optimal_slots[0]
            current_predicted_focus = self._predict_focus_for_slot(current_hour)
            
            improvement = best_slot['predicted_focus'] - current_predicted_focus
            
            if improvement > 10:  # Significant improvement
                suggestions.append({
                    'task': task,
                    'current_time': slot['start_time'],
                    'suggested_time': best_slot['slot'],
                    'improvement_percent': improvement,
                    'reason': f"Predicted {improvement:.0f}% higher focus at {best_slot['slot']}"
                })
        
        return {
            'total_suggestions': len(suggestions),
            'suggestions': suggestions,
            'overall_improvement': sum(s['improvement_percent'] for s in suggestions)
        }
    
    def _predict_focus_for_slot(self, hour: int) -> float:
        """Helper to predict focus for a given hour."""
        features = self._create_feature_vector(datetime.now(), hour)
        X_scaled = self.scaler.transform([features])
        return self.model.predict(X_scaled)[0]


# Library Requirements for Schedule Optimizer:
# - scikit-learn (RandomForestRegressor, StandardScaler)
# - pandas (data manipulation)
# - numpy (numerical operations)
# - sqlite3 (database queries)