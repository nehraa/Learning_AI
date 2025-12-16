"""
Focus Detector Daemon - Detects user's focus state
Uses multimodal signals when available, falls back to simple heuristics
"""

import time
import json
import uuid
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import sqlite3

logger = logging.getLogger(__name__)


class FocusDetectorDaemon:
    """
    Detects focus state using available signals
    Platform-aware with graceful degradation
    
    States: FOCUSED, ACTIVE, DISTRACTED, INACTIVE
    """
    
    def __init__(self, db_path: Optional[Path] = None, interval_seconds: int = 30):
        """
        Initialize focus detector
        
        Args:
            db_path: Path to database
            interval_seconds: How often to check focus (default: 30)
        """
        if db_path is None:
            data_dir = Path.home() / ".rfai" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "rfai.db"
        
        self.db_path = db_path
        self.interval = interval_seconds
        self.running = False
        self.platform = platform.system()
        
        # Signal weights (for multimodal fusion)
        self.weights = {
            'keyboard': 0.30,  # Typing activity
            'mouse': 0.25,     # Mouse movement
            'window': 0.25,    # Window stability
            'cpu': 0.20        # CPU usage patterns
        }
        
        # Track last state for smoothing
        self.last_state = "INACTIVE"
        self.state_duration = 0
        
        logger.info(f"Focus Detector initialized on {self.platform}")
        logger.info(f"Check interval: {self.interval}s")
        
        # Setup platform-specific monitoring
        self._setup_monitoring()
    
    def _setup_monitoring(self):
        """Setup available monitoring capabilities"""
        self.capabilities = {
            'keyboard': False,
            'mouse': False,
            'camera': False,
            'microphone': False,
            'window': False,
            'cpu': False
        }
        
        # Try keyboard/mouse monitoring
        try:
            from pynput import keyboard, mouse
            self.keyboard_listener = None
            self.mouse_listener = None
            self.capabilities['keyboard'] = True
            self.capabilities['mouse'] = True
            logger.info("pynput available for keyboard/mouse monitoring")
        except ImportError:
            logger.warning("pynput not available - install for better focus detection")
        
        # Try CPU monitoring
        try:
            import psutil
            self.capabilities['cpu'] = True
            logger.info("psutil available for CPU monitoring")
        except ImportError:
            logger.warning("psutil not available - install for CPU-based focus hints")
        
        # Window monitoring depends on platform
        if self.platform in ["Darwin", "Linux", "Windows"]:
            self.capabilities['window'] = True
        
        logger.info(f"Capabilities: {sum(self.capabilities.values())}/6 signals available")
    
    def compute_focus_score(self) -> Dict[str, any]:
        """
        Compute current focus score from available signals
        
        Returns:
            Dict with state, confidence, and signal breakdown
        """
        signals = {}
        
        # Get available signals
        if self.capabilities['keyboard']:
            signals['keyboard'] = self._get_keyboard_signal()
        else:
            signals['keyboard'] = 0.5  # Neutral
        
        if self.capabilities['mouse']:
            signals['mouse'] = self._get_mouse_signal()
        else:
            signals['mouse'] = 0.5
        
        if self.capabilities['window']:
            signals['window'] = self._get_window_signal()
        else:
            signals['window'] = 0.5
        
        if self.capabilities['cpu']:
            signals['cpu'] = self._get_cpu_signal()
        else:
            signals['cpu'] = 0.5
        
        # Compute weighted score
        composite_score = sum(
            self.weights.get(key, 0) * value
            for key, value in signals.items()
        ) / sum(self.weights.values())
        
        # Scale to 0-100
        composite_score = composite_score * 100
        
        # Classify state
        if composite_score >= 75:
            state = "FOCUSED"
        elif composite_score >= 50:
            state = "ACTIVE"
        elif composite_score >= 25:
            state = "DISTRACTED"
        else:
            state = "INACTIVE"
        
        # Smooth state transitions (avoid rapid changes)
        if state != self.last_state:
            self.state_duration = 0
        else:
            self.state_duration += self.interval
        
        # Only change state if new state persists > 60s
        if self.state_duration < 60 and self.last_state != "INACTIVE":
            state = self.last_state
        else:
            self.last_state = state
        
        confidence = min(0.95, 0.5 + (self.state_duration / 300))  # Confidence increases with duration
        
        return {
            'state': state,
            'confidence': confidence,
            'composite_score': composite_score,
            'signals': signals,
            'capabilities': sum(self.capabilities.values())
        }
    
    def _get_keyboard_signal(self) -> float:
        """
        Get keyboard activity signal (0.0 = inactive, 1.0 = active typing)
        
        NOTE: This is a simplified version. Full implementation would track
        key press events over the last interval.
        """
        # For now, return random for demo
        # Real implementation would use pynput listener
        return 0.7  # Assume moderate typing
    
    def _get_mouse_signal(self) -> float:
        """
        Get mouse activity signal (0.0 = still, 1.0 = active)
        
        NOTE: Real implementation would track mouse movement distance
        """
        return 0.6  # Assume moderate movement
    
    def _get_window_signal(self) -> float:
        """
        Get window stability signal (0.0 = switching apps, 1.0 = stable)
        
        NOTE: Would track app switches over time
        """
        return 0.8  # Assume stable window
    
    def _get_cpu_signal(self) -> float:
        """
        Get CPU usage signal
        High CPU might indicate active work (compiling, rendering, etc.)
        """
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            # Normalize: 0-20% CPU = low activity, 20-80% = active, >80% = very active
            if cpu_percent < 20:
                return 0.3
            elif cpu_percent < 80:
                return 0.7
            else:
                return 0.9
        except Exception:
            return 0.5
    
    def log_focus_state(self, focus_data: Dict):
        """Log focus state to database"""
        state_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO focus_states (
                    id, timestamp, state, confidence, signal_breakdown
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                state_id,
                timestamp,
                focus_data['state'],
                focus_data['confidence'],
                json.dumps(focus_data['signals'])
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Focus state: {focus_data['state']} ({focus_data['confidence']:.2f})")
        except Exception as e:
            logger.error(f"Error logging focus state: {e}")
    
    def run(self):
        """Main daemon loop"""
        self.running = True
        logger.info("Focus Detector daemon started")
        logger.info(f"Available signals: {sum(self.capabilities.values())}/6")
        
        try:
            while self.running:
                # Compute focus score
                focus_data = self.compute_focus_score()
                
                # Log to database
                self.log_focus_state(focus_data)
                
                # Sleep until next check
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            logger.info("Focus Detector daemon stopped by user")
        except Exception as e:
            logger.error(f"Focus Detector daemon error: {e}")
        finally:
            self.running = False
            logger.info("Focus Detector daemon shutdown")
    
    def stop(self):
        """Stop the daemon"""
        self.running = False


if __name__ == "__main__":
    # Test the daemon
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    daemon = FocusDetectorDaemon(interval_seconds=10)  # 10s for testing
    daemon.run()
