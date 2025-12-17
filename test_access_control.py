#!/usr/bin/env python3
"""
Test script for time-block access control system
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:5001/api"

def test_schedule():
    """Test getting current schedule"""
    print("=" * 60)
    print("TEST 1: Get Current Block")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE}/schedule/current-block")
        data = response.json()
        print(json.dumps(data, indent=2))
        return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_access_control(content_type):
    """Test access control check"""
    print(f"\n{'=' * 60}")
    print(f"TEST: Check Access for {content_type}")
    print("=" * 60)
    try:
        response = requests.get(
            f"{API_BASE}/access-control/check?content_type={content_type}"
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2))
        
        if response.status_code == 403:
            print(f"🔒 ACCESS BLOCKED - {data.get('reason')}")
        else:
            print(f"✅ ACCESS ALLOWED - {data.get('reason')}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_log_activity(session_id=None):
    """Test logging activity"""
    print(f"\n{'=' * 60}")
    print("TEST: Log Page Activity")
    print("=" * 60)
    try:
        response = requests.post(
            f"{API_BASE}/activity/log-page",
            json={
                "app_name": "Chrome",
                "page_title": "Research Paper - ArXiv",
                "page_info": {"url": "https://arxiv.org/abs/2023.01234"},
                "focus_state": "FOCUSED"
            }
        )
        data = response.json()
        print(json.dumps(data, indent=2))
        return data.get('log_id')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_session_start():
    """Test starting a session"""
    print(f"\n{'=' * 60}")
    print("TEST: Start Session")
    print("=" * 60)
    try:
        response = requests.post(
            f"{API_BASE}/time-blocks/session/start",
            json={
                "block_name": "Science Block",
                "block_type": "science_youtube_and_papers",
                "goal_duration_minutes": 180
            }
        )
        data = response.json()
        print(json.dumps(data, indent=2))
        return data.get('session_id')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_log_block_activity(session_id):
    """Test logging block activity"""
    print(f"\n{'=' * 60}")
    print("TEST: Log Block Activity")
    print("=" * 60)
    try:
        response = requests.post(
            f"{API_BASE}/activity/block-activity",
            json={
                "session_id": session_id,
                "action": "content_view",
                "content_type": "science_youtube",
                "page_title": "Quantum Computing Explained",
                "attention_score": 85
            }
        )
        data = response.json()
        print(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_session_activity(session_id):
    """Test getting session activity"""
    print(f"\n{'=' * 60}")
    print(f"TEST: Get Session Activity ({session_id})")
    print("=" * 60)
    try:
        response = requests.get(
            f"{API_BASE}/analytics/session-activity/{session_id}"
        )
        data = response.json()
        print(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n🧪 TESTING TIME-BLOCK ACCESS CONTROL SYSTEM\n")
    
    # Test 1: Get schedule info
    block_info = test_schedule()
    
    # Test 2: Check access for different content types
    content_types = [
        'science_youtube',
        'science_papers',
        'self_help_youtube',
        'movies'
    ]
    
    access_results = {}
    for ct in content_types:
        allowed = test_access_control(ct)
        access_results[ct] = allowed
    
    # Test 3: Log activity
    log_id = test_log_activity()
    
    # Test 4: Session management
    session_id = test_session_start()
    
    if session_id:
        # Test 5: Log activity during session
        test_log_block_activity(session_id)
        
        # Test 6: Get session activity
        test_session_activity(session_id)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    
    if block_info:
        active_block = block_info.get('block', {}).get('active', False)
        print(f"Active Block: {active_block}")
        if active_block:
            print(f"  - Name: {block_info['block']['name']}")
            print(f"  - Type: {block_info['block']['content_type']}")
    
    print("\nAccess Control Results:")
    for ct, allowed in access_results.items():
        status = "✅ ALLOWED" if allowed else "🔒 BLOCKED"
        print(f"  {ct}: {status}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
