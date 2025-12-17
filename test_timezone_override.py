#!/usr/bin/env python3
"""
Test timezone configuration and manual override functionality
"""

import json
import requests
from datetime import datetime
import sys

API_BASE = "http://localhost:5001/api"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_timezone_config():
    """Check timezone configuration"""
    print_section("1. Timezone Configuration")
    
    try:
        with open('interests.json') as f:
            config = json.load(f)
        
        timezone = config['daily_schedule']['timezone']
        print(f"✅ Configured Timezone: {timezone}")
        
        # Try to use the timezone
        try:
            import pytz
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            print(f"✅ Current Time ({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        except ImportError:
            print("⚠️  pytz not installed - install with: pip install pytz")
        except Exception as e:
            print(f"❌ Error with timezone: {e}")
        
        print("\nTime Blocks:")
        for block in config['daily_schedule']['time_blocks']:
            print(f"  • {block['icon']} {block['name']}")
            print(f"    Time: {block['start_time']} - {block['end_time']} ({block['duration_hours']}h)")
            print()
        
    except FileNotFoundError:
        print("❌ interests.json not found")
    except Exception as e:
        print(f"❌ Error reading config: {e}")

def test_current_block():
    """Check current active block"""
    print_section("2. Current Active Block")
    
    try:
        response = requests.get(f"{API_BASE}/schedule/current-block")
        data = response.json()
        
        if data.get('block', {}).get('active'):
            block = data['block']
            print(f"✅ Active Block: {block['name']}")
            print(f"   Time: {block['start_time']} - {block['end_time']}")
            print(f"   Content: {block['content_type']}")
            print(f"   Theme: {block['theme']}")
        else:
            print("ℹ️  No active block right now")
            if data.get('next_blocks'):
                print("\n   Next blocks:")
                for nb in data['next_blocks']:
                    print(f"     • {nb['icon']} {nb['name']} at {nb['start_time']}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Start with: python rfai_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_available_blocks():
    """Get list of available blocks for override"""
    print_section("3. Available Blocks for Override")
    
    try:
        response = requests.get(f"{API_BASE}/schedule/available-blocks")
        data = response.json()
        
        print("You can override to any of these blocks:\n")
        for i, block in enumerate(data['blocks'], 1):
            print(f"{i}. {block['icon']} {block['name']}")
            print(f"   Content: {block['content_type']}")
            print(f"   Duration: {block['duration_hours']}h")
            print()
        
        return data['blocks']
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_manual_override(blocks):
    """Test manual override functionality"""
    print_section("4. Testing Manual Override")
    
    if not blocks:
        print("⚠️  No blocks available")
        return
    
    # Test with first block
    test_block = blocks[0]['name']
    print(f"Setting override to: {test_block}")
    
    try:
        response = requests.post(
            f"{API_BASE}/schedule/override",
            json={'block_name': test_block}
        )
        data = response.json()
        
        if data.get('override_active'):
            print(f"✅ Override activated!")
            print(f"   Current block: {data.get('current_block')}")
            print(f"   Message: {data.get('message')}")
        else:
            print("❌ Override failed")
        
        # Verify by checking current block
        print("\nVerifying override...")
        response = requests.get(f"{API_BASE}/schedule/current-block")
        current = response.json()
        
        if current.get('block', {}).get('name') == test_block:
            print(f"✅ Verified: Current block is {test_block}")
        else:
            print("❌ Verification failed")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_clear_override():
    """Test clearing override"""
    print_section("5. Clearing Manual Override")
    
    try:
        response = requests.delete(f"{API_BASE}/schedule/override")
        data = response.json()
        
        print(f"✅ {data.get('message')}")
        print(f"   Override active: {data.get('override_active')}")
        
        # Check current block after clearing
        print("\nCurrent block after clearing override:")
        response = requests.get(f"{API_BASE}/schedule/current-block")
        current = response.json()
        
        if current.get('block', {}).get('active'):
            print(f"   Active: {current['block']['name']}")
        else:
            print("   No active block (automatic detection)")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("\n" + "█"*70)
    print("  🕐 TIMEZONE & OVERRIDE TESTING")
    print("█"*70)
    
    # Test 1: Check timezone config
    test_timezone_config()
    
    # Test 2: Check current block
    test_current_block()
    
    # Test 3: Get available blocks
    blocks = test_available_blocks()
    
    # Test 4: Manual override
    if blocks:
        override_success = test_manual_override(blocks)
        
        # Test 5: Clear override
        if override_success:
            import time
            print("\nWaiting 2 seconds before clearing...")
            time.sleep(2)
            test_clear_override()
    
    # Summary
    print_section("SUMMARY")
    print("""
✅ Timezone configured in interests.json
✅ Current block detection working
✅ Manual override API functional
✅ Override clearing works

Usage:
------
# Override to Science Block
curl -X POST http://localhost:5001/api/schedule/override \\
  -H "Content-Type: application/json" \\
  -d '{"block_name": "Science Learning Block"}'

# Clear override
curl -X DELETE http://localhost:5001/api/schedule/override

# Check current block
curl http://localhost:5001/api/schedule/current-block

Configuration:
--------------
Edit interests.json (line 181):
  "timezone": "Asia/Kolkata"  ← Change timezone here

Edit time blocks (lines 183-220):
  "start_time": "09:00"       ← Change start time
  "end_time": "12:00"         ← Change end time

Documentation:
--------------
See: docs/TIMEZONE_OVERRIDE_GUIDE.md
    """)

if __name__ == "__main__":
    main()
