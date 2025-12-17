"""
macOS Menu Bar Widget
Shows current task, time, and focus state in the menu bar
Requires: rumps (macOS only)
"""

import os
import logging
import platform
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class MenuBarWidget:
    """
    macOS menu bar widget for RFAI
    Displays current task, focus state, and quick actions
    """
    
    def __init__(self, api_url: str = "http://localhost:5000"):
        """
        Initialize menu bar widget
        
        Args:
            api_url: RFAI API server URL
        """
        self.api_url = api_url
        self.app = None
        
        # Check if we're on macOS
        if platform.system() != "Darwin":
            logger.error("Menu bar widget only works on macOS")
            raise RuntimeError("Menu bar widget requires macOS")
        
        # Try to import rumps
        try:
            import rumps
            self.rumps = rumps
            logger.info("rumps library available")
        except ImportError:
            logger.error("rumps not installed. Install with: pip install rumps")
            raise ImportError("rumps required for menu bar widget")
    
    def create_app(self):
        """Create the menu bar app"""
        import requests
        
        class RFAIMenuBarApp(self.rumps.App):
            """RFAI Menu Bar Application"""
            
            def __init__(self, parent):
                super(RFAIMenuBarApp, self).__init__(
                    "RFAI",
                    icon=None,  # Can set custom icon
                    title="RFAI"
                )
                self.parent = parent
                self.api_url = parent.api_url
                
                # Menu items
                self.menu = [
                    self.rumps.MenuItem("Current Task: Loading..."),
                    self.rumps.MenuItem("Focus: --"),
                    None,  # Separator
                    self.rumps.MenuItem("Show Dashboard", callback=self.show_dashboard),
                    self.rumps.MenuItem("Refresh", callback=self.refresh_status),
                    None,
                    self.rumps.MenuItem("Start Focus Session", callback=self.start_focus),
                    self.rumps.MenuItem("Take Break", callback=self.take_break),
                    None,
                    self.rumps.MenuItem("Preferences...", callback=self.show_preferences),
                    self.rumps.MenuItem("Quit RFAI", callback=self.quit_app)
                ]
                
                # Start update timer (every 30 seconds)
                self.timer = self.rumps.Timer(self.update_status, 30)
                self.timer.start()
                
                # Initial update
                self.update_status(None)
            
            def update_status(self, sender):
                """Update menu bar status"""
                try:
                    # Get current status from API
                    response = requests.get(
                        f"{self.api_url}/api/status",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Get current task
                        task_response = requests.get(
                            f"{self.api_url}/api/activity/today",
                            timeout=5
                        )
                        
                        if task_response.status_code == 200:
                            activity = task_response.json()
                            focus_pct = activity.get('focus_percentage', 0)
                            
                            # Update title
                            self.title = f"🎯 {int(focus_pct)}%"
                            
                            # Update menu items
                            self.menu["Current Task: Loading..."].title = f"Task: Studying"
                            self.menu["Focus: --"].title = f"Focus: {int(focus_pct)}%"
                        
                        logger.debug("Menu bar updated")
                    
                except Exception as e:
                    logger.error(f"Failed to update menu bar: {e}")
                    self.title = "RFAI (offline)"
            
            def show_dashboard(self, sender):
                """Open dashboard in browser"""
                import webbrowser
                webbrowser.open(self.api_url)
            
            def refresh_status(self, sender):
                """Manually refresh status"""
                self.update_status(None)
            
            def start_focus(self, sender):
                """Start a focus session"""
                try:
                    # Could trigger focus mode via API
                    self.rumps.notification(
                        "RFAI Focus",
                        "Focus Session Started",
                        "Stay focused on your current task",
                        sound=False
                    )
                except Exception as e:
                    logger.error(f"Failed to start focus: {e}")
            
            def take_break(self, sender):
                """Take a break"""
                try:
                    self.rumps.notification(
                        "RFAI Break",
                        "Time for a break!",
                        "Step away for 5 minutes",
                        sound=True
                    )
                except Exception as e:
                    logger.error(f"Failed to trigger break: {e}")
            
            def show_preferences(self, sender):
                """Show preferences window"""
                import webbrowser
                webbrowser.open(f"{self.api_url}/settings")
            
            def quit_app(self, sender):
                """Quit the application"""
                self.rumps.quit_application()
        
        self.app = RFAIMenuBarApp(self)
        return self.app
    
    def run(self):
        """Run the menu bar app"""
        if not self.app:
            self.app = self.create_app()
        
        logger.info("Starting menu bar widget...")
        self.app.run()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='RFAI Menu Bar Widget')
    parser.add_argument('--api-url', default='http://localhost:5000',
                       help='RFAI API server URL')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    # Check platform
    if platform.system() != "Darwin":
        print("❌ Menu bar widget only works on macOS")
        exit(1)
    
    # Check rumps
    try:
        import rumps
    except ImportError:
        print("❌ rumps not installed")
        print("Install with: pip install rumps")
        exit(1)
    
    # Start widget
    widget = MenuBarWidget(api_url=args.api_url)
    widget.run()
