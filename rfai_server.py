#!/usr/bin/env python3
"""
RFAI Main Server
Starts all daemons and the API server
"""

import sys
import time
import logging
import argparse
import threading
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env (if present) and normalize keys
from rfai.config.env import load_env

from database.init_db import init_database, get_db_connection
from rfai.daemons.time_tracker import TimeTrackerDaemon
from rfai.daemons.focus_detector import FocusDetectorDaemon
from rfai.daemons.attention_monitor import AttentionMonitorDaemon
from rfai.api.server import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rfai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RFAIServer:
    """Main server orchestrator"""
    
    def __init__(self, 
                 db_path=None,
                 api_host='127.0.0.1',
                 api_port=5000,
                 enable_daemons=True):
        """
        Initialize RFAI server
        
        Args:
            db_path: Path to database
            api_host: API server host (default: 127.0.0.1 for security)
            api_port: API server port
            enable_daemons: Whether to start background daemons
        """
        self.db_path = db_path
        if self.db_path is None:
            data_dir = Path.home() / ".rfai" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "rfai.db"
        
        self.api_host = api_host
        self.api_port = api_port
        self.enable_daemons = enable_daemons
        
        self.daemons = {}
        self.daemon_threads = {}
        self.running = False
        
        logger.info("=" * 60)
        logger.info("ROUTINE FOCUS AI (RFAI) - Starting")
        logger.info("=" * 60)
        logger.info(f"Database: {self.db_path}")
        logger.info(f"API: http://{api_host}:{api_port}")
        logger.info(f"Daemons enabled: {enable_daemons}")
        logger.info("=" * 60)
    
    def initialize_database(self):
        """Initialize database if needed"""
        if not self.db_path.exists():
            logger.info("Database not found, initializing...")
            success = init_database(self.db_path)
            if success:
                logger.info("✅ Database initialized successfully")
            else:
                logger.error("❌ Database initialization failed")
                return False
        else:
            logger.info("✅ Database already exists")
        
        return True
    
    def start_daemons(self):
        """Start all background daemons"""
        if not self.enable_daemons:
            logger.info("Daemons disabled, skipping...")
            return
        
        logger.info("Starting background daemons...")
        
        # Time Tracker Daemon
        try:
            self.daemons['time_tracker'] = TimeTrackerDaemon(
                db_path=self.db_path,
                interval_seconds=60
            )
            thread = threading.Thread(
                target=self.daemons['time_tracker'].run,
                daemon=True,
                name="TimeTracker"
            )
            thread.start()
            self.daemon_threads['time_tracker'] = thread
            logger.info("✅ Time Tracker daemon started")
        except Exception as e:
            logger.error(f"❌ Failed to start Time Tracker: {e}")
        
        # Focus Detector Daemon
        try:
            self.daemons['focus_detector'] = FocusDetectorDaemon(
                db_path=self.db_path,
                interval_seconds=30
            )
            thread = threading.Thread(
                target=self.daemons['focus_detector'].run,
                daemon=True,
                name="FocusDetector"
            )
            thread.start()
            self.daemon_threads['focus_detector'] = thread
            logger.info("✅ Focus Detector daemon started")
        except Exception as e:
            logger.error(f"❌ Failed to start Focus Detector: {e}")
        
        # Attention Monitor Daemon (NEW - multimodal with camera/mic)
        try:
            self.daemons['attention_monitor'] = AttentionMonitorDaemon(
                db_path=self.db_path,
                interval_seconds=5
            )
            thread = threading.Thread(
                target=self.daemons['attention_monitor'].run,
                daemon=True,
                name="AttentionMonitor"
            )
            thread.start()
            self.daemon_threads['attention_monitor'] = thread
            logger.info("✅ Attention Monitor daemon started (camera, mic, system signals)")
        except Exception as e:
            logger.error(f"❌ Failed to start Attention Monitor: {e}")
        
        # Update daemon status in database
        try:
            conn = get_db_connection(self.db_path)
            cursor = conn.cursor()
            for daemon_name in self.daemons.keys():
                cursor.execute("""
                    UPDATE daemon_status
                    SET status = 'running', 
                        last_heartbeat = datetime('now'),
                        start_time = datetime('now')
                    WHERE daemon_name = ?
                """, (daemon_name,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update daemon status: {e}")
        
        logger.info(f"Started {len(self.daemons)} daemons")
    
    def stop_daemons(self):
        """Stop all daemons"""
        logger.info("Stopping daemons...")
        
        for name, daemon in self.daemons.items():
            try:
                daemon.stop()
                logger.info(f"✅ Stopped {name}")
            except Exception as e:
                logger.error(f"❌ Error stopping {name}: {e}")
        
        # Update status in database
        try:
            conn = get_db_connection(self.db_path)
            cursor = conn.cursor()
            for daemon_name in self.daemons.keys():
                cursor.execute("""
                    UPDATE daemon_status
                    SET status = 'stopped', last_heartbeat = datetime('now')
                    WHERE daemon_name = ?
                """, (daemon_name,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update daemon status: {e}")
    
    def start_api_server(self):
        """Start Flask API server"""
        logger.info("Starting API server...")
        
        try:
            app = create_app()
            
            logger.info("=" * 60)
            logger.info("🚀 RFAI Server Ready!")
            logger.info("=" * 60)
            logger.info(f"📊 Dashboard: http://{self.api_host}:{self.api_port}")
            logger.info(f"🔌 API: http://{self.api_host}:{self.api_port}/api")
            logger.info(f"💚 Health: http://{self.api_host}:{self.api_port}/health")
            logger.info("=" * 60)
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)
            
            app.run(
                host=self.api_host,
                port=self.api_port,
                debug=False,
                use_reloader=False  # Important for daemon threads
            )
        except Exception as e:
            logger.error(f"❌ API server error: {e}")
            raise
    
    def start(self):
        """Start the complete RFAI system"""
        self.running = True
        
        # Initialize database
        if not self.initialize_database():
            logger.error("Failed to initialize database, exiting")
            return False
        
        # Start daemons
        if self.enable_daemons:
            self.start_daemons()
            # Give daemons a moment to start
            time.sleep(1)
        
        # Start API server (blocking)
        try:
            self.start_api_server()
        except KeyboardInterrupt:
            logger.info("\n\nShutdown requested...")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the complete RFAI system"""
        logger.info("Shutting down RFAI server...")
        
        self.running = False
        
        if self.enable_daemons:
            self.stop_daemons()
        
        logger.info("=" * 60)
        logger.info("✅ RFAI Server stopped successfully")
        logger.info("=" * 60)


def main():
    """Main entry point"""
    # Ensure .env is loaded before anything instantiates integrations
    load_env(override=False)

    parser = argparse.ArgumentParser(description='RFAI - Routine Focus AI Server')
    parser.add_argument('--host', default='0.0.0.0', help='API host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='API port (default: 5000)')
    parser.add_argument('--no-daemons', action='store_true', help='Disable background daemons')
    parser.add_argument('--db-path', help='Custom database path')
    
    args = parser.parse_args()
    
    # Create server
    server = RFAIServer(
        db_path=Path(args.db_path) if args.db_path else None,
        api_host=args.host,
        api_port=args.port,
        enable_daemons=not args.no_daemons
    )
    
    # Start server
    server.start()


if __name__ == '__main__':
    main()
