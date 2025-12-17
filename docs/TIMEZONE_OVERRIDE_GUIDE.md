# Time Block Configuration & Override Guide

## Quick Reference

### Where Times Are Configured
**File:** `interests.json` (Line 180-220)

```json
"daily_schedule": {
  "timezone": "Asia/Kolkata",  // ← CHANGE TIMEZONE HERE
  "time_blocks": [
    {
      "name": "Science Learning Block",
      "start_time": "09:00",      // ← CHANGE START TIME
      "end_time": "12:00",        // ← CHANGE END TIME
      "duration_hours": 3,
      "content_type": "science_youtube_and_papers",
      "theme": "dark_blue",
      "icon": "🔬"
    }
  ]
}
```

---

## 1. Changing Timezone (Indian Time)

### Update Timezone in interests.json

**Current Setting:**
```json
"timezone": "Asia/Kolkata"
```

**Common Timezones:**
- India: `"Asia/Kolkata"` (IST - UTC+5:30)
- USA East: `"America/New_York"`
- USA West: `"America/Los_Angeles"`
- UK: `"Europe/London"`
- Japan: `"Asia/Tokyo"`
- Australia: `"Australia/Sydney"`

**After changing timezone:**
```bash
# Restart server for changes to take effect
python rfai_server.py
```

---

## 2. Changing Time Block Schedules

### Edit times in interests.json

**Example: Adjust to your daily routine**

```json
"time_blocks": [
  {
    "name": "Science Learning Block",
    "start_time": "06:00",    // 6 AM IST
    "end_time": "09:00",      // 9 AM IST
    "duration_hours": 3,
    "content_type": "science_youtube_and_papers",
    "theme": "dark_blue",
    "icon": "🔬"
  },
  {
    "name": "Self-Help & Philosophy",
    "start_time": "20:00",    // 8 PM IST
    "end_time": "21:00",      // 9 PM IST
    "duration_hours": 1,
    "content_type": "self_help_youtube",
    "theme": "warm_orange",
    "icon": "🧠"
  },
  {
    "name": "Movie & Reflection",
    "start_time": "21:30",    // 9:30 PM IST
    "end_time": "23:00",      // 11 PM IST
    "duration_hours": 1.5,
    "content_type": "artistic_movies",
    "theme": "cinema_purple",
    "icon": "🎬"
  }
]
```

**Time Format:**
- Use 24-hour format: `"HH:MM"`
- Examples: `"06:00"`, `"14:30"`, `"23:45"`

**Important:**
- Recalculate `duration_hours` if you change start/end times
- Example: 06:00 to 09:00 = 3 hours

---

## 3. Manual Override (NEW!)

### Override Time Block via API

**Force a specific time block regardless of time:**

```bash
# Activate Science Block manually
curl -X POST http://localhost:5001/api/schedule/override \
  -H "Content-Type: application/json" \
  -d '{"block_name": "Science Learning Block"}'

# Response:
{
  "override_active": true,
  "current_block": "Science Learning Block",
  "message": "Override set to 'Science Learning Block'"
}
```

**Clear override (return to automatic):**
```bash
curl -X DELETE http://localhost:5001/api/schedule/override

# OR using POST with null:
curl -X POST http://localhost:5001/api/schedule/override \
  -H "Content-Type: application/json" \
  -d '{"block_name": null}'
```

**Get available blocks to override:**
```bash
curl http://localhost:5001/api/schedule/available-blocks

# Response:
{
  "blocks": [
    {
      "name": "Science Learning Block",
      "content_type": "science_youtube_and_papers",
      "icon": "🔬",
      "duration_hours": 3
    },
    {
      "name": "Self-Help & Philosophy",
      "content_type": "self_help_youtube",
      "icon": "🧠",
      "duration_hours": 1
    },
    {
      "name": "Movie & Reflection",
      "content_type": "artistic_movies",
      "icon": "🎬",
      "duration_hours": 1.5
    }
  ]
}
```

---

## 4. Python Examples

### Override from Python Script

```python
import requests

API_BASE = "http://localhost:5001/api"

# Activate Science Block
response = requests.post(
    f"{API_BASE}/schedule/override",
    json={"block_name": "Science Learning Block"}
)
print(response.json())

# Check current block
response = requests.get(f"{API_BASE}/schedule/current-block")
print(response.json()['block']['name'])

# Clear override later
response = requests.delete(f"{API_BASE}/schedule/override")
print(response.json())
```

### Check Timezone Configuration

```python
import json

# Load config
with open('interests.json') as f:
    config = json.load(f)

timezone = config['daily_schedule']['timezone']
print(f"Current timezone: {timezone}")

# List all time blocks
for block in config['daily_schedule']['time_blocks']:
    print(f"{block['name']}: {block['start_time']}-{block['end_time']}")
```

---

## 5. Dashboard Override Button (Coming Soon)

**Planned Feature:**
Add override buttons to dashboard:

```html
<button onclick="overrideBlock('Science Learning Block')">
  🔬 Force Science Block
</button>
<button onclick="clearOverride()">
  🔓 Clear Override
</button>
```

---

## 6. Use Cases for Manual Override

### Scenario 1: Want to Study Outside Schedule
```bash
# It's 11 PM but you want to study science
curl -X POST http://localhost:5001/api/schedule/override \
  -d '{"block_name": "Science Learning Block"}'

# Now dashboard shows science content
# Access control allows science videos/papers
# Attention monitor tracks as science session
```

### Scenario 2: Testing Different Content
```bash
# Test movie recommendations without waiting
curl -X POST http://localhost:5001/api/schedule/override \
  -d '{"block_name": "Movie & Reflection"}'

# Dashboard now shows movie recommendations
```

### Scenario 3: Flexible Schedule
```bash
# Your schedule changed today, manually control blocks:

# Morning: Study session
curl -X POST http://localhost:5001/api/schedule/override \
  -d '{"block_name": "Science Learning Block"}'

# Afternoon: Self-help
curl -X POST http://localhost:5001/api/schedule/override \
  -d '{"block_name": "Self-Help & Philosophy"}'

# Evening: Clear and let automatic mode resume
curl -X DELETE http://localhost:5001/api/schedule/override
```

---

## 7. How Timezone Detection Works

### Automatic Timezone Handling

```python
# From time_block_content.py
timezone_str = config.get('daily_schedule', {}).get('timezone', 'UTC')
local_tz = pytz.timezone(timezone_str)
now = datetime.now(local_tz)
current_time = now.strftime("%H:%M")
```

**Process:**
1. Reads timezone from `interests.json`
2. Converts current time to that timezone
3. Compares against time block schedules
4. Returns active block or None

**Fallback:**
If timezone parsing fails, falls back to system local time (UTC)

---

## 8. Testing Your Configuration

### Test Script

```python
#!/usr/bin/env python3
"""Test timezone and time block configuration"""

import json
import requests
from datetime import datetime
import pytz

# Load config
with open('interests.json') as f:
    config = json.load(f)

# Check timezone
timezone_str = config['daily_schedule']['timezone']
print(f"Configured Timezone: {timezone_str}")

# Get current time in that timezone
try:
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    print(f"Current Time ({timezone_str}): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
except Exception as e:
    print(f"Error with timezone: {e}")

# Check current block from API
response = requests.get('http://localhost:5001/api/schedule/current-block')
data = response.json()

if data.get('block', {}).get('active'):
    block = data['block']
    print(f"\nActive Block: {block['name']}")
    print(f"Time: {block['start_time']} - {block['end_time']}")
    print(f"Content Type: {block['content_type']}")
else:
    print("\nNo active block")
    print("Next blocks:")
    for next_block in data.get('next_blocks', []):
        print(f"  - {next_block['icon']} {next_block['name']} at {next_block['start_time']}")

# Test override
print("\n--- Testing Manual Override ---")
override_response = requests.post(
    'http://localhost:5001/api/schedule/override',
    json={'block_name': 'Science Learning Block'}
)
print(override_response.json())

# Check again
response = requests.get('http://localhost:5001/api/schedule/current-block')
print(f"After override: {response.json()['block']['name']}")

# Clear override
clear_response = requests.delete('http://localhost:5001/api/schedule/override')
print(f"\nCleared: {clear_response.json()}")
```

**Run:**
```bash
python test_timezone.py
```

---

## 9. Common Issues & Solutions

### Issue: Wrong Timezone Showing

**Problem:** Times don't match Indian Standard Time

**Solution:**
1. Check `interests.json` line 181:
   ```json
   "timezone": "Asia/Kolkata"
   ```
2. Restart server: `python rfai_server.py`
3. Verify: `curl http://localhost:5001/api/schedule/current-block`

### Issue: Time Blocks Not Activating

**Problem:** No block shown even during scheduled time

**Solutions:**
1. **Check time format:**
   - Use 24-hour format: `"09:00"` not `"9:00 AM"`
   - Include leading zeros: `"06:00"` not `"6:00"`

2. **Check end time > start time:**
   ```json
   "start_time": "09:00",  // Must be before end_time
   "end_time": "12:00"
   ```

3. **Install pytz:**
   ```bash
   pip install pytz
   ```

### Issue: Override Not Working

**Problem:** Manual override doesn't activate block

**Solutions:**
1. **Check exact block name:**
   ```bash
   # Get available blocks first
   curl http://localhost:5001/api/schedule/available-blocks
   
   # Use exact name from response
   curl -X POST http://localhost:5001/api/schedule/override \
     -d '{"block_name": "Science Learning Block"}'
   ```

2. **Check server logs:**
   ```bash
   tail -f rfai.log
   ```

---

## 10. Configuration Examples

### Example 1: Early Morning Learner (India)

```json
"daily_schedule": {
  "timezone": "Asia/Kolkata",
  "time_blocks": [
    {
      "name": "Science Learning Block",
      "start_time": "05:00",  // 5 AM IST
      "end_time": "08:00",
      "duration_hours": 3
    },
    {
      "name": "Self-Help & Philosophy",
      "start_time": "19:00",  // 7 PM IST
      "end_time": "20:00",
      "duration_hours": 1
    },
    {
      "name": "Movie & Reflection",
      "start_time": "21:00",  // 9 PM IST
      "end_time": "22:30",
      "duration_hours": 1.5
    }
  ]
}
```

### Example 2: Night Owl (India)

```json
"daily_schedule": {
  "timezone": "Asia/Kolkata",
  "time_blocks": [
    {
      "name": "Science Learning Block",
      "start_time": "22:00",  // 10 PM IST
      "end_time": "01:00",    // 1 AM IST (next day)
      "duration_hours": 3,
      "content_type": "science_youtube_and_papers"
    }
  ]
}
```

**Note:** Overnight blocks (crossing midnight) may need special handling.

### Example 3: Weekend Schedule

Create separate config file `interests_weekend.json`:

```json
"daily_schedule": {
  "timezone": "Asia/Kolkata",
  "time_blocks": [
    {
      "name": "Extended Science Block",
      "start_time": "10:00",
      "end_time": "14:00",  // 4 hours on weekends
      "duration_hours": 4
    }
  ]
}
```

---

## 11. API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/schedule/current-block` | GET | Get current active block |
| `/api/schedule/full-day` | GET | Get all time blocks |
| `/api/schedule/override` | POST | Set manual override |
| `/api/schedule/override` | DELETE | Clear manual override |
| `/api/schedule/available-blocks` | GET | List all blocks for override |

---

## 12. Quick Commands Reference

```bash
# Check current timezone configuration
cat interests.json | grep timezone

# Check current block
curl http://localhost:5001/api/schedule/current-block | jq '.block.name'

# Override to Science Block
curl -X POST http://localhost:5001/api/schedule/override \
  -H "Content-Type: application/json" \
  -d '{"block_name": "Science Learning Block"}'

# Clear override
curl -X DELETE http://localhost:5001/api/schedule/override

# Get all available blocks
curl http://localhost:5001/api/schedule/available-blocks | jq '.blocks[].name'

# Restart server after config changes
pkill -f rfai_server.py && python rfai_server.py
```

---

## Summary

✅ **Timezone:** Changed to `Asia/Kolkata` (Indian Standard Time)
✅ **Times:** Edit in `interests.json` lines 180-220
✅ **Override:** Use API to manually activate any time block
✅ **Flexible:** Works with or without manual override

**Next Steps:**
1. Edit `interests.json` to set your preferred times
2. Restart server
3. Test with `curl http://localhost:5001/api/schedule/current-block`
4. Use override API when you want to study outside schedule

---

**Last Updated:** 2024-12-17
**Version:** 2.1
