# Time-Block Access Control System (Soft-Lock)

## Overview

The time-block access control system implements a **soft-lock** mechanism that restricts content access during active learning blocks while allowing full access during inactive periods.

### Key Concept: "Soft-Lock"

- **During Active Block**: Only content matching the current time block's type is accessible
  - Example: During 09:00-12:00 Science block, only science YouTube videos and research papers are allowed
  - Movies and self-help content show a 403 "Access Blocked" response
  
- **During Inactive Periods**: Full access to all content types
  - Between time blocks: User can access any content freely
  - Outside all time blocks: No restrictions

- **Benefit**: Encourages focused learning while providing flexibility outside active blocks

## Time Block Types & Allowed Content

```
TIME BLOCK                  ALLOWED CONTENT
─────────────────────────────────────────────
09:00-12:00 Science         • Science YouTube videos
(3 hours)                   • Research papers (ArXiv, etc.)
                            • Blocked: Movies, Self-help

13:00-14:00 Self-Help       • Self-help YouTube videos
(1 hour)                    • Blocked: Science, Movies

18:00-19:30 Movies          • Artistic movies
(1.5 hours)                 • Blocked: Science, Self-help
```

## API Endpoints

### 1. Check Access (`GET /api/access-control/check`)

**Check if user can access specific content type**

```bash
curl "http://localhost:5001/api/access-control/check?content_type=science_youtube"
```

**Response (Access Allowed):**
```json
{
  "access_allowed": true,
  "reason": "Accessing allowed content for Science Block",
  "lock_active": true,
  "current_block": {
    "name": "Science Block",
    "content_type": "science_youtube_and_papers",
    "start_time": "09:00",
    "end_time": "12:00",
    "theme": "dark_blue"
  },
  "attention_required": 0.7
}
```

**Response (Access Denied - HTTP 403):**
```json
{
  "access_allowed": false,
  "reason": "Content locked during Science Block",
  "lock_active": true,
  "current_block": {...},
  "allowed_content": "science_youtube_and_papers",
  "requested_content": "movies"
}
```

**Response (No Active Block - Full Access):**
```json
{
  "access_allowed": true,
  "reason": "No active time block - unrestricted access",
  "lock_active": false,
  "current_block": null
}
```

**Query Parameters:**
- `content_type` (required): One of:
  - `science_youtube`
  - `science_papers`
  - `self_help_youtube`
  - `movies`

---

### 2. Log Page Activity (`POST /api/activity/log-page`)

**Log the current app/page activity**

```bash
curl -X POST "http://localhost:5001/api/activity/log-page" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "Chrome",
    "page_title": "Quantum Computing - ArXiv",
    "page_info": {
      "url": "https://arxiv.org/abs/2023.01234",
      "tab_index": 0
    },
    "focus_state": "FOCUSED"
  }'
```

**Response:**
```json
{
  "logged": true,
  "log_id": "a1b2c3d4-e5f6-4789-0123-456789abcdef"
}
```

**Request Body:**
- `app_name` (required): Application name (e.g., "Chrome", "Safari")
- `page_title` (required): Current page/document title
- `page_info` (optional): Additional metadata (URL, tab info, etc.)
- `focus_state` (optional): Focus classification (FOCUSED, ACTIVE, DISTRACTED, INACTIVE)

---

### 3. Log Block Activity (`POST /api/activity/block-activity`)

**Log specific activities during active time blocks**

```bash
curl -X POST "http://localhost:5001/api/activity/block-activity" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-uuid-here",
    "action": "content_view",
    "content_type": "science_youtube",
    "page_title": "Quantum Mechanics Basics",
    "attention_score": 85
  }'
```

**Response:**
```json
{
  "logged": true,
  "session_id": "session-uuid-here",
  "action": "content_view"
}
```

**Request Body:**
- `session_id` (required): Active session ID
- `action` (required): Action type:
  - `content_view`: User viewed content
  - `content_completed`: User finished content
  - `pause`: User paused/took break
  - `distraction_detected`: Attention monitor detected distraction
  - `goal_reached`: User reached session goal
- `content_type` (required): Type of content being accessed
- `page_title` (required): Title of content viewed
- `attention_score` (optional): Current attention score (0-100)

---

### 4. Get Session Activity (`GET /api/analytics/session-activity/<session_id>`)

**Retrieve all activities logged during a session**

```bash
curl "http://localhost:5001/api/analytics/session-activity/session-uuid-here"
```

**Response:**
```json
{
  "session_id": "session-uuid-here",
  "activities": [
    {
      "timestamp": "2024-01-15 09:05:12",
      "action": "content_view",
      "content_type": "science_youtube",
      "page_title": "Quantum Mechanics Basics",
      "attention_score": 85
    },
    {
      "timestamp": "2024-01-15 09:08:34",
      "action": "distraction_detected",
      "content_type": "science_youtube",
      "page_title": "Quantum Mechanics Basics",
      "attention_score": 42
    }
  ],
  "content_consumed": [
    {
      "content_id": "content-uuid",
      "content_type": "science_youtube",
      "title": "Quantum Mechanics Basics",
      "metadata_json": "{\"timestamp\": \"2024-01-15T09:05:12\"}"
    }
  ],
  "total_activities": 2,
  "total_content_items": 1
}
```

---

## Dashboard UI Features

### Access Control Panel

The dashboard now shows a real-time **Access Control Panel** that updates based on the current time block state.

**During Active Block:**
```
🔒 Soft-Lock: Science Block
───────────────────────────
⏱️ Time block active! Content is locked to Science Block for 
focused learning until 12:00.

📺 Science YouTube - ✓ Allowed
📄 Science Papers - ✓ Allowed
📺 Self-Help YouTube - ✗ Blocked
🎬 Movies - ✗ Blocked
```

**During Inactive Period:**
```
🔓 Unrestricted Access
───────────────────────
✅ No active time block - you can access any content.

📺 YouTube Allowed
📄 Papers Allowed
🎬 Movies Allowed
```

### Features

1. **Real-time Lock Status**: Shows 🔒 (locked) or 🔓 (unlocked) icon
2. **Content Restrictions**: Visual indicators for allowed/blocked content
3. **Block Info**: Current active block name and end time
4. **Auto-Updates**: Refreshes every 30 seconds
5. **Color Coding**:
   - 🟢 Green border/background: Content allowed
   - 🔴 Red border/background: Content blocked

---

## Database Tables

### `block_activity_log`
Tracks all activities performed during active time blocks
```sql
CREATE TABLE block_activity_log (
  id INTEGER PRIMARY KEY,
  session_id TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  action TEXT,           -- content_view, pause, distraction_detected, etc.
  content_type TEXT,     -- science_youtube, movies, etc.
  page_title TEXT,
  attention_score REAL,
  FOREIGN KEY (session_id) REFERENCES time_block_sessions(id)
);
```

### `session_content_log`
Tracks content consumed during sessions
```sql
CREATE TABLE session_content_log (
  id INTEGER PRIMARY KEY,
  session_id TEXT NOT NULL,
  content_id TEXT,
  content_type TEXT,
  title TEXT,
  metadata_json TEXT,
  FOREIGN KEY (session_id) REFERENCES time_block_sessions(id)
);
```

### `time_logs` (Enhanced)
Now includes page/app tracking:
```sql
CREATE TABLE time_logs (
  id TEXT PRIMARY KEY,
  timestamp DATETIME,
  actual_app TEXT,           -- Active application name
  page_title TEXT,           -- Current page/document title
  page_info_json TEXT,       -- URL, metadata, etc.
  focus_state TEXT,
  duration_seconds INTEGER
);
```

---

## Integration Examples

### Example 1: Check Access Before Playing Video

```javascript
// User tries to play a movie during Science block
async function playVideo(videoType) {
  const allowed = await checkContentAccess(videoType);
  
  if (!allowed) {
    showBlockedMessage("Movies are locked during Science block");
    return;
  }
  
  // Proceed with playback
  startVideoPlayback();
}
```

### Example 2: Session Activity Tracking

```python
# In time_tracker.py daemon
def track_activity():
    while True:
        app = get_active_window()
        page = get_page_title()
        
        # Log the activity
        requests.post("http://localhost:5001/api/activity/log-page", 
            json={
                "app_name": app,
                "page_title": page,
                "focus_state": "ACTIVE"
            }
        )
        
        sleep(60)
```

### Example 3: Full Session Workflow

```python
# 1. Start a session
session = requests.post("http://localhost:5001/api/time-blocks/session/start",
    json={
        "block_name": "Science Block",
        "block_type": "science_youtube_and_papers",
        "goal_duration_minutes": 180
    }
).json()

session_id = session['session_id']

# 2. During session, log activities
requests.post("http://localhost:5001/api/activity/block-activity",
    json={
        "session_id": session_id,
        "action": "content_view",
        "content_type": "science_youtube",
        "page_title": "Quantum Physics",
        "attention_score": 87
    }
)

# 3. Get analytics after session
analytics = requests.get(
    f"http://localhost:5001/api/analytics/session-activity/{session_id}"
).json()

print(f"Activities: {len(analytics['activities'])}")
print(f"Content items: {len(analytics['content_consumed'])}")
```

---

## Testing the System

Run the provided test script:

```bash
python test_access_control.py
```

This will test:
1. Get current schedule and active block
2. Check access for all content types
3. Log page activity
4. Start a session
5. Log block activities
6. Retrieve session analytics

---

## Key Benefits

✅ **Focused Learning**: Soft-lock encourages staying on topic during active blocks
✅ **Flexibility**: No restrictions during inactive periods
✅ **Activity Tracking**: Complete audit trail of what user accessed and when
✅ **Attention Correlation**: Link content access to attention scores
✅ **Session Analytics**: Detailed breakdown of session performance

---

## Future Enhancements

- [ ] Configurable access control rules per time block
- [ ] Break/interrupt management (allow brief off-topic access)
- [ ] Content recommendations based on attention score
- [ ] Gamification: Streaks of focused sessions
- [ ] Mobile app support for access control
- [ ] Calendar integration for dynamic scheduling

---

**Last Updated**: 2024-01-15
**Status**: ✅ Production Ready
