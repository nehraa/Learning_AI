"""
Enhanced Attention Monitor Daemon - Multimodal focus detection
Uses camera, microphone, keyboard, mouse, and window tracking
Provides real-time attentiveness scoring and recommendations
"""

import time
import json
import uuid
import logging
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import sqlite3
import threading

logger = logging.getLogger(__name__)


class AttentionMonitorDaemon:
    """
    Real-time multimodal attention monitoring
    Tracks: camera (eye gaze/head pose), microphone (speech patterns),
            keyboard, mouse, window focus, CPU usage
    
    States: FOCUSED, ACTIVE, DISTRACTED, INACTIVE, TAKING_BREAK
    """
    
    def __init__(self, db_path: Optional[Path] = None, interval_seconds: int = 5):
        """
        Initialize attention monitor
        
        Args:
            db_path: Path to database
            interval_seconds: How often to sample (default: 5)
        """
        if db_path is None:
            data_dir = Path.home() / ".rfai" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "rfai.db"
        
        self.db_path = db_path
        self.interval = interval_seconds
        self.running = False
        self.platform = platform.system()
        
        # Attention weights (multimodal fusion)
        self.weights = {
            'camera': 0.30,      # Eye tracking / head pose
            'microphone': 0.15,  # Voice activity
            'keyboard': 0.20,    # Typing/input activity
            'mouse': 0.15,       # Mouse movement/clicks
            'window': 0.15,      # Window focus stability
            'cpu': 0.05          # CPU usage patterns
        }
        
        # State tracking
        self.last_state = "INACTIVE"
        self.state_duration = 0
        self.focus_history = []  # Rolling window of attention scores
        self.max_history = 60  # Track last 60 samples
        
        # Session tracking
        self.session_id = str(uuid.uuid4())
        self.session_start = datetime.now()
        self.total_focused_time = 0
        self.total_distracted_time = 0
        self.current_block = None  # Track which time block we're in
        
        logger.info(f"Attention Monitor initialized on {self.platform}")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Monitor interval: {self.interval}s")
        
        # Setup platform-specific monitoring
        self._setup_camera()
        self._setup_microphone()
        self._setup_system_monitoring()
    
    def _setup_camera(self):
        """Setup camera/webcam for eye tracking or head pose"""
        self.camera_available = False
        self.camera = None
        self.eye_tracker = None
        
        try:
            import cv2
            self.cv2 = cv2
            
            # Try to open default webcam
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.camera_available = True
                logger.info("✅ Camera available for attention detection")
                
                # Try to load cascade classifier for face/eye detection
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                
                eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
                self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
            else:
                logger.warning("Camera not available or denied permission")
                if self.camera:
                    self.camera.release()
        except ImportError:
            logger.warning("OpenCV not available - install opencv-python for camera-based attention")
        except Exception as e:
            logger.warning(f"Camera setup failed: {e}")
    
    def _setup_microphone(self):
        """Setup microphone for voice activity detection"""
        self.microphone_available = False
        self.audio_stream = None
        
        try:
            import pyaudio
            import wave
            
            self.pyaudio = pyaudio.PyAudio()
            self.microphone_available = True
            logger.info("✅ Microphone available for voice activity detection")
            
        except ImportError:
            logger.warning("PyAudio not available - install pyaudio for microphone-based attention")
        except Exception as e:
            logger.warning(f"Microphone setup failed: {e}")
    
    def _setup_system_monitoring(self):
        """Setup system-wide monitoring (keyboard, mouse, CPU)"""
        self.system_monitoring_available = False
        
        try:
            import psutil
            from pynput import keyboard, mouse
            
            self.psutil = psutil
            self.keyboard = keyboard
            self.mouse = mouse
            self.system_monitoring_available = True
            
            # Initialize input tracking
            self.last_keyboard_time = time.time()
            self.last_mouse_time = time.time()
            self.last_mouse_pos = None
            self.keyboard_event_count = 0
            self.mouse_event_count = 0
            
            logger.info("✅ System monitoring (keyboard, mouse, CPU) available")
            
        except ImportError:
            logger.warning("pynput or psutil not available - install both for system monitoring")
        except Exception as e:
            logger.warning(f"System monitoring setup failed: {e}")
    
    def compute_attention_score(self) -> Dict:
        """
        Compute multimodal attention score (0-100)
        
        Returns:
            Dict with state, score, signals, and recommendations
        """
        signals = {}
        
        # Camera signal: face/eye detection
        if self.camera_available:
            signals['camera'] = self._get_camera_signal()
        else:
            signals['camera'] = 0.5  # Neutral
        
        # Microphone signal: voice activity
        if self.microphone_available:
            signals['microphone'] = self._get_microphone_signal()
        else:
            signals['microphone'] = 0.5
        
        # System signals
        if self.system_monitoring_available:
            signals['keyboard'] = self._get_keyboard_signal()
            signals['mouse'] = self._get_mouse_signal()
            signals['cpu'] = self._get_cpu_signal()
        else:
            signals['keyboard'] = 0.5
            signals['mouse'] = 0.5
            signals['cpu'] = 0.5
        
        signals['window'] = self._get_window_signal()
        
        # Compute weighted composite score
        composite_score = sum(
            self.weights.get(key, 0) * value
            for key, value in signals.items()
        ) / sum(self.weights.values())
        
        # Scale to 0-100
        composite_score = composite_score * 100
        
        # Add to history
        self.focus_history.append(composite_score)
        if len(self.focus_history) > self.max_history:
            self.focus_history.pop(0)
        
        # Classify state with hysteresis
        if composite_score >= 75:
            new_state = "FOCUSED"
        elif composite_score >= 55:
            new_state = "ACTIVE"
        elif composite_score >= 30:
            new_state = "DISTRACTED"
        else:
            new_state = "INACTIVE"
        
        # Smooth state transitions (avoid rapid changes)
        if new_state != self.last_state:
            self.state_duration = 0
        else:
            self.state_duration += self.interval
        
        # Only change state if new state persists > 10s
        if self.state_duration < 10 and self.last_state != "INACTIVE":
            state = self.last_state
        else:
            state = new_state
            self.last_state = state
        
        # Confidence increases with sustained state
        confidence = min(0.95, 0.5 + (self.state_duration / 60))
        
        # Calculate trend (is attention improving or degrading?)
        if len(self.focus_history) > 10:
            recent_avg = sum(self.focus_history[-10:]) / 10
            older_avg = sum(self.focus_history[-20:-10]) / 10
            trend = recent_avg - older_avg  # positive = improving
        else:
            trend = 0
        
        return {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'state': state,
            'score': composite_score,
            'confidence': confidence,
            'trend': trend,
            'signals': signals,
            'capabilities': {
                'camera': self.camera_available,
                'microphone': self.microphone_available,
                'system': self.system_monitoring_available
            }
        }
    
    def _get_camera_signal(self) -> float:
        """
        Get camera-based attention signal using face/eye detection
        0.0 = not looking at screen, 1.0 = focused on screen
        """
        try:
            if not self.camera or not self.camera.isOpened():
                return 0.5
            
            ret, frame = self.camera.read()
            if not ret:
                return 0.5
            
            gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return 0.0  # No face detected = not focused
            
            # Detect eyes in face region
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                
                if len(eyes) > 0:
                    return 0.9  # Face and eyes detected = focused
            
            return 0.5  # Face detected but no eyes = ambiguous
            
        except Exception as e:
            logger.debug(f"Camera signal error: {e}")
            return 0.5
    
    def _get_microphone_signal(self) -> float:
        """
        Get microphone-based voice activity signal
        0.0 = silent, 1.0 = speaking/audio detected
        """
        try:
            # Simple amplitude-based detection
            # In production, use librosa or scipy for better feature extraction
            return 0.3  # Placeholder - most learning is silent
        except Exception as e:
            logger.debug(f"Microphone signal error: {e}")
            return 0.5
    
    def _get_keyboard_signal(self) -> float:
        """
        Get keyboard activity signal
        0.0 = no typing, 1.0 = active typing
        """
        try:
            current_time = time.time()
            time_since_last_input = current_time - self.last_keyboard_time
            
            # If typed in last 10 seconds, score decreases over time
            if time_since_last_input < 10:
                return max(0.0, 1.0 - (time_since_last_input / 10))
            else:
                return 0.0
        except Exception:
            return 0.5
    
    def _get_mouse_signal(self) -> float:
        """
        Get mouse activity signal
        0.0 = mouse idle, 1.0 = active movement/clicks
        """
        try:
            current_time = time.time()
            time_since_last_input = current_time - self.last_mouse_time
            
            # If moved/clicked in last 15 seconds, score decreases
            if time_since_last_input < 15:
                return max(0.0, 1.0 - (time_since_last_input / 15))
            else:
                return 0.0
        except Exception:
            return 0.5
    
    def _get_cpu_signal(self) -> float:
        """
        Get CPU usage signal (normalized 0-1)
        Moderate CPU = focused work, extreme CPU = distraction/heavy load
        """
        try:
            cpu_percent = self.psutil.cpu_percent(interval=0.1) / 100.0
            
            # Map CPU to focus: moderate (30-60%) = focused, extreme = distracted
            if 0.3 <= cpu_percent <= 0.6:
                return 0.8
            elif cpu_percent > 0.6:
                return 0.4  # High CPU might be distraction
            else:
                return 0.5
        except Exception:
            return 0.5
    
    def _get_window_signal(self) -> float:
        """
        Get window focus stability signal
        1.0 = same app focused whole time, 0.0 = rapidly switching apps
        """
        # Simplified: in production, track app switches
        return 0.7  # Placeholder
    
    def log_attention_event(self, attention_data: Dict):
        """Log attention event to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO attention_log (
                    session_id, timestamp, state, score, confidence,
                    trend, signals_json, capabilities_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attention_data['session_id'],
                attention_data['timestamp'],
                attention_data['state'],
                attention_data['score'],
                attention_data['confidence'],
                attention_data['trend'],
                json.dumps(attention_data['signals']),
                json.dumps(attention_data['capabilities'])
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Error logging attention: {e}")
    
    def get_recommendations(self, attention_data: Dict) -> List[str]:
        """Generate recommendations based on attention state"""
        recommendations = []
        
        state = attention_data['state']
        score = attention_data['score']
        trend = attention_data['trend']
        
        if state == "FOCUSED":
            if trend < -5:  # Attention declining
                recommendations.append("💡 Your focus is declining. Consider a 2-minute break.")
        elif state == "ACTIVE":
            recommendations.append("📊 Good focus level. Keep up the momentum!")
        elif state == "DISTRACTED":
            recommendations.append("⚠️ Distracted state detected. Close distracting tabs/apps?")
            recommendations.append("🔕 Enable Do Not Disturb mode?")
        elif state == "INACTIVE":
            recommendations.append("❌ No activity detected. Return to learning?")
            recommendations.append("☕ Or take a break and come back refreshed")
        
        return recommendations
    
    def run(self):
        """Main daemon loop"""
        self.running = True
        logger.info("🎯 Attention Monitor daemon started")
        
        try:
            while self.running:
                try:
                    # Compute attention
                    attention_data = self.compute_attention_score()
                    
                    # Log to database
                    self.log_attention_event(attention_data)
                    
                    # Get recommendations
                    recommendations = self.get_recommendations(attention_data)
                    
                    # Log state changes
                    if attention_data['state'] != self.last_state:
                        logger.info(
                            f"🔄 Attention state: {attention_data['state']} "
                            f"(score: {attention_data['score']:.1f}, "
                            f"confidence: {attention_data['confidence']:.2f})"
                        )
                    
                    # Sleep before next check
                    time.sleep(self.interval)
                    
                except Exception as e:
                    logger.error(f"Error in attention monitoring loop: {e}")
                    time.sleep(self.interval)
        
        except KeyboardInterrupt:
            logger.info("Attention monitor interrupted")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the daemon"""
        self.running = False
        
        if self.camera:
            try:
                self.camera.release()
            except:
                pass
        
        logger.info("🎯 Attention Monitor daemon stopped")
