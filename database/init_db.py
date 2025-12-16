"""
Database Initialization Script
Creates and initializes the RFAI database with complete schema
"""

import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database(db_path=None):
    """Initialize the database with schema"""
    if db_path is None:
        # Default location
        data_dir = Path.home() / ".rfai" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "rfai.db"
    
    logger.info(f"Initializing database at: {db_path}")
    
    # Read schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Create database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Execute schema
        cursor.executescript(schema_sql)
        conn.commit()
        logger.info("Database schema created successfully")
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Created {len(tables)} tables")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False
    finally:
        conn.close()

def get_db_connection(db_path=None):
    """Get a connection to the database"""
    if db_path is None:
        data_dir = Path.home() / ".rfai" / "data"
        db_path = data_dir / "rfai.db"
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

if __name__ == "__main__":
    # Initialize database
    success = init_database()
    if success:
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
