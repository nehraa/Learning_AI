"""
Enhanced Focus Detector with Camera/MediaPipe Support
Uses multimodal signals including camera pose/gaze detection
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


class EnhancedFocusDetector:
    """
    Advanced focus detection using multimodal signals
    Supports camera (MediaPipe), keyboard, mouse, window, CPU
    """
    
    def __init__(self, db_path: Optional[Path] = None, interval_seconds: int = 30,
                 use_camera: bool = False, use_microphone: bool = False):
        """
        Initialize enhanced focus detector
        
        Args:
            db_path: Path to database
            interval_seconds: How often to check focus
            use_camera: Enable camera-based focus detection
            use_microphone: Enable microphone-based focus detection
        """
        if db_path is None:
            data_dir = Path.home() / ".rfai" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "rfai.db"
        
        self.db_path = db_path
        self.interval = interval_seconds
        self.running = False
        self.platform = platform.system()
        
        self.use_camera = use_camera
        self.use_microphone = use_microphone
        
        # Signal weights (for multimodal fusion)
        self.weights = {
            'keyboard': 0.15,  # Typing activity
            'mouse': 0.15,     # Mouse movement
            'window': 0.15,    # Window stability
            'cpu': 0.10,       # CPU usage patterns
            'pose': 0.25,      # Body posture (camera)
            'gaze': 0.20       # Eye gaze (camera)
        }
        
        # Track last state for smoothing
        self.last_state = "INACTIVE"
        self.state_duration = 0
        
        logger.info(f"Enhanced Focus Detector initialized on {self.platform}")
        logger.info(f"Camera: {use_camera}, Microphone: {use_microphone}")
        
        # Setup monitoring capabilities
        self._setup_monitoring()
        
        # Setup camera if enabled
        if use_camera:
            self._setup_camera()
    
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
            logger.warning("psutil not available")
        
        # Window monitoring depends on platform
        if self.platform in ["Darwin", "Linux", "Windows"]:
            self.capabilities['window'] = True
        
        logger.info(f"Capabilities: {sum(self.capabilities.values())}/6 signals available")
    
    def _setup_camera(self):
        """Setup camera with MediaPipe"""
        try:
            import cv2
            import mediapipe as mp
            
            self.cv2 = cv2
            self.mp = mp
            
            # Initialize MediaPipe
            self.mp_pose = mp.solutions.pose
            self.mp_face_mesh = mp.solutions.face_mesh
            
            self.pose = self.mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Try to open camera
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.capabilities['camera'] = True
                logger.info("✓ Camera initialized with MediaPipe")
            else:
                logger.warning("Camera not accessible")
                self.use_camera = False
        
        except ImportError as e:
            logger.warning(f"MediaPipe/OpenCV not available: {e}")
            logger.warning("Install with: pip install mediapipe opencv-python")
            self.use_camera = False
        except Exception as e:
            logger.error(f"Camera setup failed: {e}")
            self.use_camera = False
    
    def _get_pose_signal(self) -> float:
        """
        Get body pose signal from camera
        Returns 0.0 (distracted) to 1.0 (focused)
        """
        if not self.use_camera or not self.capabilities.get('camera'):
            return 0.5  # Neutral
        
        try:
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                return 0.5
            
            # Convert to RGB
            frame_rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
            
            # Process pose
            results = self.pose.process(frame_rgb)
            
            if not results.pose_landmarks:
                return 0.3  # No person detected
            
            # Analyze posture
            landmarks = results.pose_landmarks.landmark
            
            # Check if sitting upright (shoulders level)
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            
            shoulder_diff = abs(left_shoulder.y - right_shoulder.y)
            
            # Good posture if shoulders are level (< 0.05 difference)
            if shoulder_diff < 0.05:
                return 0.9  # Focused posture
            elif shoulder_diff < 0.1:
                return 0.7  # Okay posture
            else:
                return 0.4  # Poor posture (distracted)
        
        except Exception as e:
            logger.debug(f"Pose detection error: {e}")
            return 0.5
    
    def _get_gaze_signal(self) -> float:
        """
        Get gaze direction signal from camera
        Returns 0.0 (looking away) to 1.0 (looking at screen)
        """
        if not self.use_camera or not self.capabilities.get('camera'):
            return 0.5  # Neutral
        
        try:
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                return 0.5
            
            # Convert to RGB
            frame_rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
            
            # Process face mesh
            results = self.face_mesh.process(frame_rgb)
            
            if not results.multi_face_landmarks:
                return 0.3  # No face detected
            
            # Analyze gaze (simplified - check if face is centered)
            face_landmarks = results.multi_face_landmarks[0]
            landmarks = face_landmarks.landmark
            
            # Get nose tip (landmark 1)
            nose = landmarks[1]
            
            # Check if nose is centered (0.4-0.6 range horizontally)
            if 0.4 <= nose.x <= 0.6 and 0.4 <= nose.y <= 0.6:
                return 0.9  # Looking at screen
            elif 0.3 <= nose.x <= 0.7:
                return 0.6  # Slightly off-center
            else:
                return 0.3  # Looking away
        
        except Exception as e:
            logger.debug(f"Gaze detection error: {e}")
            return 0.5
    
    def compute_focus_score(self) -> Dict[str, any]:
        """
        Compute current focus score from all available signals
        
        Returns:
            Dict with state, confidence, and signal breakdown
        """
        signals = {}
        
        # Get all available signals
        if self.capabilities.get('keyboard'):
            signals['keyboard'] = self._get_keyboard_signal()
        
        if self.capabilities.get('mouse'):
            signals['mouse'] = self._get_mouse_signal()
        
        if self.capabilities.get('window'):
            signals['window'] = self._get_window_signal()
        
        if self.capabilities.get('cpu'):
            signals['cpu'] = self._get_cpu_signal()
        
        if self.use_camera and self.capabilities.get('camera'):
            signals['pose'] = self._get_pose_signal()
            signals['gaze'] = self._get_gaze_signal()
        
        # Compute weighted score
        total_weight = sum(self.weights.get(k, 0) for k in signals.keys())
        composite_score = sum(
            self.weights.get(key, 0) * value
            for key, value in signals.items()
        ) / total_weight if total_weight > 0 else 0.5
        
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
        
        # Smooth state transitions
        if state != self.last_state:
            self.state_duration = 0
        else:
            self.state_duration += self.interval
        
        # Only change state if new state persists > 60s
        if self.state_duration < 60 and self.last_state != "INACTIVE":
            state = self.last_state
        else:
            self.last_state = state
        
        confidence = min(0.95, 0.5 + (self.state_duration / 300))
        
        return {
            'state': state,
            'confidence': confidence,
            'composite_score': composite_score,
            'signals': signals,
            'capabilities': sum(self.capabilities.values())
        }
    
    def _get_keyboard_signal(self) -> float:
        """Keyboard activity signal"""
        return 0.7  # Placeholder - real implementation would track key presses
    
    def _get_mouse_signal(self) -> float:
        """Mouse activity signal"""
        return 0.6  # Placeholder - real implementation would track mouse distance
    
    def _get_window_signal(self) -> float:
        """Window stability signal"""
        return 0.8  # Placeholder - real implementation would track app switches
    
    def _get_cpu_signal(self) -> float:
        """CPU usage signal"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent < 20:
                return 0.3
            elif cpu_percent < 80:
                return 0.7
            else:
                return 0.9
        except:
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
            
            logger.debug(f"Focus: {focus_data['state']} ({focus_data['confidence']:.2f})")
        except Exception as e:
            logger.error(f"Error logging focus state: {e}")
    
    def run(self):
        """Main daemon loop"""
        self.running = True
        logger.info("Enhanced Focus Detector daemon started")
        logger.info(f"Signals: {sum(self.capabilities.values())}/6")
        
        try:
            while self.running:
                # Compute focus score
                focus_data = self.compute_focus_score()
                
                # Log to database
                self.log_focus_state(focus_data)
                
                # Sleep until next check
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            logger.info("Enhanced Focus Detector stopped by user")
        except Exception as e:
            logger.error(f"Enhanced Focus Detector error: {e}")
        finally:
            self.running = False
            if self.use_camera and hasattr(self, 'camera'):
                self.camera.release()
            logger.info("Enhanced Focus Detector shutdown")
    
    def stop(self):
        """Stop the daemon"""
        self.running = False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test with camera disabled by default
    daemon = EnhancedFocusDetector(interval_seconds=10, use_camera=False)
    daemon.run()
