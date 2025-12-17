"""
RFAI Daemon Processes
Background services for time tracking, focus detection, and activity monitoring
"""

from .time_tracker import TimeTrackerDaemon
from .focus_detector import FocusDetectorDaemon

__all__ = [
    'TimeTrackerDaemon',
    'FocusDetectorDaemon',
]
