"""
RFAI API Server
Flask-based REST API for all system features
"""

from .server import create_app

__all__ = ['create_app']
