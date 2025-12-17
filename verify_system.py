#!/usr/bin/env python3
"""
RFAI System Readiness Check
Verifies all components before starting the server
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    required = (3, 8)
    if version >= required:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} < {required[0]}.{required[1]}")
        return False

def check_dependencies():
    """Check installed dependencies"""
    dependencies = {
        'flask': 'Web server framework',
        'flask_cors': 'CORS support',
        'cv2': 'Computer vision (camera)',
        'pyaudio': 'Audio input (microphone)',
        'pynput': 'Keyboard/mouse tracking',
        'psutil': 'System metrics',
    }
    
    print("\n📦 Checking Dependencies:")
    all_ok = True
    for module, desc in dependencies.items():
        try:
            __import__(module)
            print(f"  ✅ {module:20} - {desc}")
        except ImportError:
            if module in ['cv2', 'pyaudio']:
                print(f"  ⚠️  {module:20} - {desc} (optional)")
            else:
                print(f"  ❌ {module:20} - {desc}")
                all_ok = False
    
    return all_ok

def check_configuration():
    """Check configuration files"""
    print("\n⚙️  Checking Configuration:")
    
    config_file = Path('interests.json')
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
            
            # Verify structure
            required_keys = ['daily_schedule', 'visual_themes', 'youtube_interests']
            for key in required_keys:
                if key in config:
                    print(f"  ✅ interests.json has '{key}'")
                else:
                    print(f"  ❌ interests.json missing '{key}'")
                    return False
            
            return True
        except Exception as e:
            print(f"  ❌ Error reading interests.json: {e}")
            return False
    else:
        print(f"  ❌ interests.json not found")
        return False

def check_database():
    """Check database initialization"""
    print("\n💾 Checking Database:")
    
    db_path = Path.home() / '.rfai' / 'data' / 'rfai.db'
    
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table count
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table'
            """)
            table_count = cursor.fetchone()[0]
            
            if table_count >= 15:
                print(f"  ✅ Database initialized with {table_count} tables")
                conn.close()
                return True
            else:
                print(f"  ⚠️  Database has only {table_count} tables (expected 20+)")
                conn.close()
                return False
        except Exception as e:
            print(f"  ❌ Error checking database: {e}")
            return False
    else:
        print(f"  ⚠️  Database not found at {db_path}")
        print(f"     It will be created on first run")
        return True

def check_file_structure():
    """Check essential file structure"""
    print("\n📁 Checking File Structure:")
    
    required_files = [
        'rfai_server.py',
        'rfai/__init__.py',
        'rfai/api/server.py',
        'rfai/daemons/time_tracker.py',
        'rfai/daemons/focus_detector.py',
        'rfai/daemons/attention_monitor.py',
        'rfai/ui/static/dashboard_enhanced.html',
        'database/schema.sql',
        'database/init_db.py',
    ]
    
    all_ok = True
    for file in required_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} not found")
            all_ok = False
    
    return all_ok

def main():
    print("\n" + "="*60)
    print("🧪 RFAI SYSTEM READINESS CHECK")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
        ("File Structure", check_file_structure),
        ("Database", check_database),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error during {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_passed = all(result for _, result in results)
    
    for name, result in results:
        status = "✅ PASS" if result else "⚠️  WARN"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    
    if all_passed:
        print("✅ System is ready! You can start the server:")
        print("   python rfai_server.py")
    else:
        print("⚠️  Some checks failed. Please review above.")
    
    print("\n📊 Dashboard: http://localhost:5001/static/dashboard_enhanced.html")
    print("📚 API Docs: http://localhost:5001/api/status")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
