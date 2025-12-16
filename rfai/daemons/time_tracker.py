"""
Time Tracker Daemon - Logs activity and app usage
Cross-platform with platform-specific implementations
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


class TimeTrackerDaemon:
    """
    Tracks active applications and time spent
    Platform-aware implementation
    """
    
    def __init__(self, db_path: Optional[Path] = None, interval_seconds: int = 60):
        """
        Initialize time tracker
        
        Args:
            db_path: Path to database (default: ~/.rfai/data/rfai.db)
            interval_seconds: How often to sample activity (default: 60)
        """
        if db_path is None:
            data_dir = Path.home() / ".rfai" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "rfai.db"
        
        self.db_path = db_path
        self.interval = interval_seconds
        self.running = False
        self.platform = platform.system()
        
        logger.info(f"Time Tracker initialized on {self.platform}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Sampling interval: {self.interval}s")
        
        # Platform-specific setup
        if self.platform == "Darwin":  # macOS
            self._setup_macos()
        elif self.platform == "Linux":
            self._setup_linux()
        elif self.platform == "Windows":
            self._setup_windows()
        else:
            logger.warning(f"Unsupported platform: {self.platform}")
    
    def _setup_macos(self):
        """Setup macOS-specific libraries"""
        try:
            from AppKit import NSWorkspace
            self.workspace = NSWorkspace.sharedWorkspace()
            self.platform_ready = True
            logger.info("macOS AppKit ready")
        except ImportError:
            logger.error("AppKit not available - install pyobjc-framework-Cocoa")
            self.platform_ready = False
    
    def _setup_linux(self):
        """Setup Linux-specific libraries"""
        try:
            # Try to import X11 libraries for window detection
            # For now, we'll use a simpler approach
            import subprocess
            self.platform_ready = True
            logger.info("Linux platform ready (using subprocess)")
        except Exception as e:
            logger.error(f"Linux setup failed: {e}")
            self.platform_ready = False
    
    def _setup_windows(self):
        """Setup Windows-specific libraries"""
        try:
            import win32gui
            import win32process
            self.platform_ready = True
            logger.info("Windows win32 ready")
        except ImportError:
            logger.error("win32gui not available - install pywin32")
            self.platform_ready = False
    
    def get_active_window(self) -> Dict[str, str]:
        """
        Get currently active window information
        
        Returns:
            Dict with app_name, window_title, process_name
        """
        if not self.platform_ready:
            return self._get_fallback_info()
        
        if self.platform == "Darwin":
            return self._get_active_window_macos()
        elif self.platform == "Linux":
            return self._get_active_window_linux()
        elif self.platform == "Windows":
            return self._get_active_window_windows()
        else:
            return self._get_fallback_info()
    
    def _get_active_window_macos(self) -> Dict[str, str]:
        """Get active window on macOS"""
        try:
            active_app = self.workspace.frontmostApplication()
            return {
                "app_name": active_app.localizedName(),
                "window_title": "",  # Would need Accessibility API
                "process_name": active_app.localizedName()
            }
        except Exception as e:
            logger.error(f"Error getting macOS window: {e}")
            return self._get_fallback_info()
    
    def _get_active_window_linux(self) -> Dict[str, str]:
        """Get active window on Linux"""
        try:
            import subprocess
            # Use xdotool if available
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                window_title = result.stdout.strip()
                # Try to get process name
                result2 = subprocess.run(
                    ['xdotool', 'getactivewindow', 'getwindowpid'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result2.returncode == 0:
                    pid = result2.stdout.strip()
                    # Get process name from pid
                    try:
                        with open(f'/proc/{pid}/comm', 'r') as f:
                            process_name = f.read().strip()
                    except:
                        process_name = "unknown"
                    
                    return {
                        "app_name": process_name,
                        "window_title": window_title,
                        "process_name": process_name
                    }
            
            return self._get_fallback_info()
        except Exception as e:
            logger.debug(f"xdotool not available: {e}")
            return self._get_fallback_info()
    
    def _get_active_window_windows(self) -> Dict[str, str]:
        """Get active window on Windows"""
        try:
            import win32gui
            import win32process
            import psutil
            
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except:
                process_name = "unknown"
            
            return {
                "app_name": process_name,
                "window_title": window_title,
                "process_name": process_name
            }
        except Exception as e:
            logger.error(f"Error getting Windows window: {e}")
            return self._get_fallback_info()
    
    def _get_fallback_info(self) -> Dict[str, str]:
        """Fallback when platform detection not available"""
        return {
            "app_name": "unknown",
            "window_title": "unknown",
            "process_name": "unknown"
        }
    
    def log_activity(self, window_info: Dict[str, str]):
        """Log activity to database"""
        log_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO time_logs (
                    id, timestamp, actual_app, duration_seconds, 
                    focus_state, focus_confidence
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                timestamp,
                window_info['app_name'],
                self.interval,
                'ACTIVE',  # Default, will be updated by focus detector
                0.5
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Logged activity: {window_info['app_name']}")
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def run(self):
        """Main daemon loop"""
        self.running = True
        logger.info("Time Tracker daemon started")
        
        try:
            while self.running:
                # Get current active window
                window_info = self.get_active_window()
                
                # Log to database
                self.log_activity(window_info)
                
                # Sleep until next sample
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            logger.info("Time Tracker daemon stopped by user")
        except Exception as e:
            logger.error(f"Time Tracker daemon error: {e}")
        finally:
            self.running = False
            logger.info("Time Tracker daemon shutdown")
    
    def stop(self):
        """Stop the daemon"""
        self.running = False


if __name__ == "__main__":
    # Test the daemon
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    daemon = TimeTrackerDaemon(interval_seconds=10)  # 10s for testing
    daemon.run()
