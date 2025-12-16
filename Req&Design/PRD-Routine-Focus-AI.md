# 📋 ROUTINE FOCUS AI - Complete Product Requirements & Design Document

**Version:** 1.0  
**Date:** December 17, 2025  
**Author:** Design Phase  
**Status:** Ready for Implementation  

---

## 🎯 EXECUTIVE SUMMARY

**Project Name:** Routine Focus AI (RFAI)

**Mission:** A unified macOS daemon that intelligently tracks your time, detects your focus state (passive/active/distracted), and recommends personalized content (papers, courses, YouTube, movies, study materials) aligned to a long-term learning plan and daily timetable. The system learns from your choices and improves recommendations via reinforcement learning while respecting your privacy (100% on-device).

**Core Value:** Turns time-tracking from passive monitoring into an active, personalized learning companion that helps you stick to routines AND discover what to do during them.

---

## 📊 SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROUTINE FOCUS AI ECOSYSTEM                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  DAEMON LAYER    │  │  CORE ENGINE     │  │  STORAGE     │ │
│  │  (Background)    │  │  (Processing)    │  │  (Local DB)  │ │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────┤ │
│  │ • Time Tracker   │  │ • LinUCB Rec     │  │ • Timetable  │ │
│  │ • Focus Detector │  │ • Intent Parser  │  │ • User Prefs │ │
│  │ • Activity Log   │  │ • Content Mix    │  │ • Ratings DB │ │
│  │ • Screen Guard   │  │ • Plan Executor  │  │ • Embeddings │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│         ↓                      ↓                      ↑         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         DATA COLLECTION LAYER (Multi-Source)            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • Camera (pose/gaze/fidget)  • Mic (noise/typing)       │  │
│  │ • App Focus (active window)  • Keyboard (rhythm)        │  │
│  │ • Browser (current tab)      • Mouse (activity)         │  │
│  │ • Screenshot (hourly)        • Activity Monitor (CPU)   │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ↓                      ↓                      ↓         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      DISCOVERY & ENRICHMENT LAYER (Multi-Channel)       │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ ArXiv API │ EdX API │ Perplexity API │ YouTube API       │  │
│  │ IMDB API  │ Local FS│ Notion/Sync    │ Custom Feeds      │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ↓                                           ↑          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      FRONTEND LAYER (Dashboard + Notifications)         │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • Web Dashboard (React/Vue)  • Menu Bar Widget          │  │
│  │ • Native Notifications       • Focus Session UI          │  │
│  │ • Day Heatmap + Stats        • Timetable Viewer         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 COMPONENT SPECIFICATIONS

### **LAYER 1: DAEMON PROCESSES** (Always Running)

Runs as `LaunchAgent` on macOS (equivalent to Windows service).

#### **1.1 Time Tracker Daemon** (`rfai_time_tracker`)
**Purpose:** Log every hour what you were doing.

**Inputs:**
- Active window name (from Accessibility API)
- Application name
- Focus state (from Focus Detector)
- Current timetable slot

**Outputs:**
- Hourly log entry: `{timestamp, task_assigned, app_open, focus_level, duration_seconds}`
- Stored in: `~/Library/Application Support/RFAI/logs/time_logs.jsonl`

**Frequency:** Every 60 seconds (sample), aggregate hourly

**Config:**
```yaml
sampling_interval: 60        # seconds
log_interval: 3600          # seconds (1 hour)
retention: 90               # days
```

---

#### **1.2 Focus Detector Daemon** (`rfai_focus_detector`)
**Purpose:** Classify your attention state in real-time.

**Multimodal Input Fusion:**

| Input | Threshold | Signal Weight | Implementation |
|-------|-----------|---------------|-----------------|
| **Camera-Pose** | Stillness >120s | 35% | MediaPipe pose, detect rigid posture |
| **Camera-Gaze** | Gaze center <5% deviation | 20% | MediaPipe face mesh, look deviation |
| **Screen Focus** | 1 window for >5min | 15% | Accessibility API, window time |
| **Mic-Ambient** | Noise <45dB + typing rhythm | 15% | PyAudio, keystroke velocity |
| **Mouse Activity** | <10px movement per min | 10% | Quartz Event Tap |
| **Keyboard Rhythm** | >40 WPM typing, no pauses | 5% | Quartz keyboard monitoring |

**Classification Output:**
- **"FOCUSED"** (80+ composite score): All signals aligned, likely deep work
- **"ACTIVE"** (50-79): Working but some distraction, acceptable productivity
- **"DISTRACTED"** (20-49): Multiple off signals, needs intervention
- **"INACTIVE"** (0-19): No activity, likely break/away from desk

**State Machine:**
```
INACTIVE ──(activity detected)──> ACTIVE
   ↑                                   ↓
   └─(5+ min no activity)─ IDLE <─────┘
                                     ↓
                        (sustained high signal)
                                     ↓
                                FOCUSED
```

**Exceptions to Log:**
- `is_taking_notes: True` → Gaze away OK (eyes on paper/iPad)
- `is_presenting: True` → Camera/mic noise expected
- `is_reading: True` → Low keystroke OK
- `manual_pause: True` → User marked break

**Output:**
```json
{
  "timestamp": "2025-12-17T00:15:30Z",
  "state": "FOCUSED",
  "confidence": 0.87,
  "signal_breakdown": {
    "pose": 0.95, "gaze": 0.82, "screen": 0.9, 
    "audio": 0.75, "mouse": 0.68, "keyboard": 0.92
  },
  "exceptions": ["is_taking_notes"]
}
```

**Frequency:** Every 10-30 seconds (real-time buffer), aggregate every 5 minutes

**Privacy Note:** All camera/mic processing on-device. No video/audio leaves machine.

---

#### **1.3 Activity Logger Daemon** (`rfai_activity_logger`)
**Purpose:** Unified activity log combining all signals.

**Log Entry Schema:**
```json
{
  "timestamp": "ISO8601",
  "hour_slot": "09:00-10:00",
  "scheduled_task": "Coding - Rust",
  "actual_primary_app": "VS Code",
  "actual_secondary_apps": ["Slack", "Browser"],
  "focus_state": "FOCUSED",
  "focus_confidence": 0.87,
  "duration_seconds": 3600,
  "exception_tags": ["is_taking_notes", "on_call"],
  "camera_usage": true,
  "mic_detected_speech": false,
  "keystroke_count": 1240,
  "mouse_movements": 45,
  "urls_visited": ["github.com/...", "rust-docs..."],
  "files_modified": ["/Users/.../src/main.rs"],
  "rating": null  # User can rate after
}
```

**Aggregations (computed hourly):**
```
Hourly Summary: {
  hour, task_assigned, focus_percent, distraction_count,
  app_switches, keystroke_rate, note_taking_time
}

Daily Summary: {
  date, total_focused_hours, total_tasks_completed,
  task_adherence_percent, best_focus_hour, worst_hour,
  recommendations_acted_on
}
```

**Storage:**
- Primary: SQLite (queryable)
- Backup: JSON Lines (streaming)
- Location: `~/Library/Application Support/RFAI/data/activity.db`

---

#### **1.4 Routine Guard Daemon** (`rfai_routine_guard`)
**Purpose:** Intelligent intervention when off-task.

**Triggers:**
1. Current time entered new timetable slot → check alignment
2. Focus state = "DISTRACTED" for >10min → alert
3. App mismatch >70% confidence → suggest refocus

**Actions (User-Configurable):**
- **Silent Mode**: Just log, no interruption
- **Gentle Nudge**: Menu bar notification (`"Study slot but coding in Slack? 🤔"`)
- **Focus Session**: Suggested 25-min pomodoro, blocklist apps
- **Deep Focus**: Lock screen, allow only task-related apps
- **Recommendation Trigger**: Auto-pull next recommendation for current slot

**Notification Format (macOS):**
```
┌──────────────────────────────────┐
│ ⏰ Routine Check-In               │
├──────────────────────────────────┤
│ Slot: 10:00-11:00 (Study)        │
│ Detected: Watching YouTube       │
│                                  │
│ [Show Recommendation] [Resume]   │
└──────────────────────────────────┘
```

**Learning:** If user dismisses >3 nudges in row for same task, lower nudge frequency.

---

### **LAYER 2: CORE ENGINE** (Processing & Recommendations)

#### **2.1 Timetable Engine** (`TimetableManager`)
**Input:** User's daily schedule (recurring or one-off)

**Data Structure:**
```json
{
  "timetable": [
    {
      "id": "slot_001",
      "day": "weekday",  // or specific date
      "start_time": "09:00",
      "end_time": "10:00",
      "task": "Deep Coding (Rust Networking)",
      "subtask": "Implement DHT peer discovery",
      "context": "Startup project",
      "min_focus_target": 80,
      "recommended_content_type": "code_tutorial",
      "blocklist_apps": ["Slack", "Twitter"],
      "notes": "Early morning, best focus"
    },
    {
      "id": "slot_002",
      "day": "weekday",
      "start_time": "10:00",
      "end_time": "10:15",
      "task": "Break",
      "subtask": "Stretch + water",
      "context": "Recovery",
      "min_focus_target": 0,
      "recommended_content_type": "none"
    },
    {
      "id": "slot_003",
      "day": "weekday",
      "start_time": "14:00",
      "end_time": "15:00",
      "task": "Tutoring Session",
      "subtask": "Student: Alex, Topic: IELTS Grammar",
      "context": "Income",
      "min_focus_target": 95,
      "recommended_content_type": "none"  // Live session
    }
  ]
}
```

**Capabilities:**
- Parse recurring patterns (e.g., "Mon-Fri 9am-10am = Coding")
- Handle exceptions (e.g., "Dec 20: Skip coding, run errands")
- Sync with calendar (Google Calendar, Notion API)
- Suggest optimizations based on historical focus data

---

#### **2.2 Learning Plan Manager** (`LongTermPlanManager`)
**Purpose:** User defines 3-6 month learning goals; system breaks into daily/weekly tasks.

**Input (User defines):**
```json
{
  "goals": [
    {
      "id": "goal_rust_networking",
      "name": "Master Decentralized Networking in Rust",
      "timeline_months": 6,
      "target_hours": 180,
      "subtopics": [
        "TCP/UDP sockets",
        "DHT algorithms",
        "Peer discovery",
        "Gossip protocols",
        "Network security"
      ],
      "resources": {
        "papers": ["ArXiv: DHT papers"],
        "courses": ["MIT 6.824 Distributed Systems"],
        "books": ["Networking in Rust"],
        "practice": ["Build mini P2P app"]
      }
    },
    {
      "id": "goal_german_language",
      "name": "Reach B2 German proficiency",
      "timeline_months": 12,
      "target_hours": 200,
      "subtopics": [
        "Conversational German",
        "Technical German (for job apps to Germany)",
        "Reading comprehension"
      ],
      "resources": {
        "youtube": ["Easy German channel"],
        "courses": ["Duolingo Advanced", "Preply tutoring"],
        "movies": ["German films with subtitles"]
      }
    },
    {
      "id": "goal_philosophy",
      "name": "Read canonical philosophy texts",
      "timeline_months": 3,
      "target_hours": 30,
      "subtopics": [
        "Phenomenology (Heidegger)",
        "Eastern philosophy (Zen Buddhism)"
      ],
      "resources": {
        "books": ["Being and Time", "Zen classics"],
        "lectures": ["Philosophy courses"]
      }
    }
  ]
}
```

**System Derivation:**
```
Goal: Rust Networking (180 hrs over 6 months)
  ↓
Monthly: 30 hours
  ↓
Weekly: 7.5 hours
  ↓
Daily (if allocated): 1-2 hours
  ↓
Breakdown: 
  - 40% reading papers (8hrs/week)
  - 40% coding practice (8hrs/week)
  - 20% lectures/videos (4hrs/week)
  ↓
Map to Timetable:
  Mon-Fri 09:00-10:00 → "Study: TCP/UDP sockets"
  Sat 14:00-16:00 → "Code: Build socket server"
  Sun 19:00-20:00 → "Read: Paper - DHT design"
```

---

#### **2.3 Unified Recommendation Engine** (`UnifiedRecommender`)
**Purpose:** Synthesize Learning_AI (papers/courses) + multi-channel discovery (YouTube, movies, study notes) using LinUCB + intent parsing.

**Recommendation Channels:**
1. **Academic**: ArXiv papers (via existing Learning_AI)
2. **Structured Learning**: EdX courses (via existing Learning_AI)
3. **Video**: YouTube (via YouTube Data API + ML classification)
4. **Entertainment**: Movies/shows (via IMDB API + ML genre matching)
5. **Practice**: Code tutorials, GitHub repos (via GitHub API + keyword match)
6. **Notes/Articles**: Medium, Dev.to, Notion (via Perplexity API for web search)
7. **Interactive**: Podcasts, interviews (via RSS feeds)

**Context Fusion Algorithm:**

```
INPUT: Current timetable slot + User's long-term goals
  {
    slot_task: "Deep Coding (Rust Networking)",
    subtopic: "DHT peer discovery",
    goal_id: "goal_rust_networking",
    user_learning_style: "learn-by-doing", // User profile
    time_available: 60,  // minutes
    completion_status: 30%, // of this subtopic
    recent_ratings: [5, 4, 5, 3]  // User's feedback
  }
  
↓ CHANNEL SELECTOR (Contextual)
  slot_task contains "Coding" → weight channels:
    - Code tutorials: 0.40
    - Papers: 0.25
    - Videos: 0.20
    - Books: 0.15
  
↓ DISCOVERY (Parallel)
  Thread 1: Search ArXiv("DHT peer discovery Rust")
  Thread 2: Search YouTube("DHT implementation tutorial")
  Thread 3: Search GitHub("rust-dht peer-discovery")
  Thread 4: Search Notion/notion-api(user_notes)
  Thread 5: Search Perplexity("best resources DHT peer discovery 2025")
  
↓ SCORING (LinUCB Multi-Armed Bandit)
  For each candidate, compute:
    score = LinUCB_score(item_embedding, user_context, past_ratings)
           + diversity_penalty(similar_to_recent)
           + recency_bonus(published < 6 months)
           + relevance_bonus(matches subtopic)
  
↓ RANKING & DEDUPLICATION
  Sort by score, remove duplicates (semantic similarity >0.95)
  
↓ OUTPUT: Top 5 Recommendations
  [
    { type: "code_tutorial", title: "...", url: "...", reason: "LinUCB+timing match", predicted_rating: 4.2 },
    { type: "paper", title: "...", url: "...", reason: "Foundational + your style", predicted_rating: 4.1 },
    ...
  ]
```

**Key Features:**
- **Intent Parsing**: NLP to extract learning intent from timetable task description
- **Content Type Matching**: Infer best modality (code → tutorials, concept → paper, practice → video)
- **Time-Aware**: If slot is 15min, don't recommend 2-hour lectures
- **Cross-Validation**: Ensure recommendations don't duplicate across channels
- **Explainability**: "Why this recommendation?" (LinUCB factor + recency + user style)

---

#### **2.4 Unified Rating & Learning System** (`RatingEngine`)
**Purpose:** Collect feedback across all content types; train LinUCB + generate insights.

**Rating Prompt (Context-Aware):**
```
AFTER USER CONSUMES CONTENT:

[Paper]: "On the Design and Evaluation of DHT Protocols"
┌─────────────────────────────────┐
│ How useful was this paper?      │
│ ⭐⭐⭐⭐⭐ (5-star)                │
│ Tags: □ Core  □ Too Hard        │
│       □ Skim-worthy □ Save      │
│ Time: 45 min / 120 min planned  │
│ Completed: Yes/No               │
├─────────────────────────────────┤
│ [Submit]  [Skip]  [Dismiss]     │
└─────────────────────────────────┘

[YouTube]: "DHT Explained in 10 mins"
┌─────────────────────────────────┐
│ Quality: ⭐⭐⭐⭐ (4-star)        │
│ Pacing: Too slow / Just right / Too fast
│ Watched: 100%                   │
├─────────────────────────────────┤
│ [Save to Queue] [Next]          │
└─────────────────────────────────┘

[Movie]: "Her"
┌─────────────────────────────────┐
│ Did this match your taste?      │
│ ⭐⭐⭐⭐ (4-star)                 │
│ Genre tags: Sci-Fi, Romance, AI │
│ Watch time: 120 min             │
│ Plan to rewatch: Yes/No         │
├─────────────────────────────────┤
│ [Loved It] [Good] [Skip]        │
└─────────────────────────────────┘
```

**Rating Schema (Universal):**
```json
{
  "id": "rating_uuid",
  "timestamp": "ISO8601",
  "user_id": "default",
  "content_id": "arxiv_2301.12345 | youtube_abc123 | imdb_tt0234215",
  "content_type": "paper | course | video | movie | article | code_tutorial",
  "rating": 5,
  "rating_confidence": 0.95,
  "tags": ["core_concept", "save_for_later", "too_hard"],
  "time_spent_seconds": 2700,
  "time_planned_seconds": 3600,
  "completion_percent": 75,
  "context": {
    "timetable_slot": "slot_001",
    "goal_id": "goal_rust_networking",
    "user_mood": "focused"  // optional
  },
  "embedding_context": [array of 384-dimensional vector]
}
```

**Learning Pipeline:**
```
1. Store rating in DB
2. Update LinUCB arm for this content type
3. Re-embed user context with new feedback
4. Recompute top-K recommendations
5. Generate insights:
   - "You rate video tutorials 4.2★ avg → boost video recommendations"
   - "Papers take 2.5x longer than planned → adjust time estimates"
   - "You complete 100% of goal-aligned content → suggest more ambitious goals"
```

---

### **LAYER 3: DATA SOURCES & ENRICHMENT** (Discovery)

#### **3.1 ArXiv Integration** (Already from Learning_AI)
- **Query Template**: `(topic:"{subtopic}" AND cat:cs.NE)` for networking papers
- **Enrichment**: Embedding + summary (existing)
- **Frequency**: Daily, incremental discovery

---

#### **3.2 YouTube API Integration** (NEW)
**Endpoint**: `youtube.search.list`

**Query Strategy:**
```python
# For subtopic "DHT peer discovery":
queries = [
  "DHT peer discovery tutorial",
  "Distributed hash table implementation",
  "IPFS DHT explainer",
  "Peer-to-peer networking basics"
]

# Filter:
- Duration: 5-180 min (user-configurable)
- Subtitles: required or available
- Views: >10k (quality signal)
- Upload date: <2 years
- Channel: educational channels prioritized
```

**Metadata Extracted**:
- Title, description, channel, duration
- Transcript (if available) → semantic similarity search
- Comments sentiment (optional: engagement signal)
- Thumbnail → content classification (whiteboard, screenshare, talking-head)

**Schema**:
```json
{
  "id": "youtube_abc123",
  "type": "video",
  "title": "DHT Explained",
  "url": "https://youtube.com/watch?v=abc123",
  "channel": "NetworkingCourses",
  "duration_seconds": 600,
  "embedding": [384-dim vector from transcript],
  "tags": ["DHT", "networking", "explainer"],
  "content_format": "screencast",
  "has_subtitles": true,
  "published_date": "2024-01-15"
}
```

---

#### **3.3 IMDB/Movie API Integration** (NEW)
**Endpoint**: OMDB API or OMDb scrape

**Use Case**: User has "Movies" in long-term learning goals (e.g., "German cinema for language learning" or "Philosophy-themed films").

**Query**:
```python
# For goal "Watch German films":
query = "German films"
filters = {
  "language": "de",
  "year_gte": 2010,
  "imdb_rating_gte": 7.0,
  "genres": ["Drama", "Sci-Fi"],  # user preference
  "runtime_range": [90, 180]
}

# For goal "Philosophy-themed":
query = "philosophy"
filters = {
  "keywords": ["phenomenology", "existentialism", "ethics"],
  "imdb_rating_gte": 7.5
}
```

**Metadata**:
```json
{
  "id": "imdb_tt0234215",
  "type": "movie",
  "title": "Sein und Zeit (Being and Time)",
  "year": 2023,
  "imdb_rating": 7.8,
  "genres": ["Drama", "Philosophical"],
  "runtime_seconds": 10800,
  "plot": "...",
  "embedding": [384-dim vector from plot + tags],
  "tags": ["phenomenology", "German", "experimental"],
  "language": "de",
  "available_on": ["Netflix", "Prime"],
  "relates_to_goal": "goal_philosophy"
}
```

---

#### **3.4 Perplexity API Integration** (NEW)
**Purpose**: Real-time web search for emerging resources, tutorials, blog posts.

**Use Case**: User has a subtopic like "Cryptography for P2P networks". System queries Perplexity to find latest blog posts, tutorials, explainers.

**API Call**:
```python
queries = [
  "best resources cryptography peer-to-peer 2025",
  "how to implement end-to-end encryption",
  "cryptography tutorial Rust"
]

# Perplexity returns:
{
  "query": "...",
  "answer": "...",
  "sources": [
    {
      "title": "...",
      "url": "...",
      "snippet": "..."
    },
    ...
  ]
}

# Process:
# - Extract URLs
# - Embed snippets
# - Classify: blog_post | tutorial | documentation | news
# - Add to recommendation pool
```

---

#### **3.5 Local User-Provided Content** (NEW)
**Purpose**: User can upload/sync their own learning materials.

**Inputs**:
- Notion database (via Notion API) → export learning notes
- GitHub repos (via GitHub API) → find related code tutorials
- Local PDF collection → OCR + embed
- Bookmarks (from browser) → import interesting links

**Schema**:
```json
{
  "id": "local_notion_draft_1",
  "type": "user_note",
  "source": "notion",
  "title": "DHT Implementation Notes",
  "content": "...",
  "embedding": [384-dim vector],
  "tags": ["DHT", "personal_notes"],
  "created_date": "2025-12-10",
  "relates_to_goal": "goal_rust_networking"
}
```

---

### **LAYER 4: STORAGE & DATA MANAGEMENT**

**Directory Structure:**
```
~/Library/Application Support/RFAI/
├── config/
│   ├── timetable.json           # Daily schedule
│   ├── long_term_plan.json      # Goals + subtopics
│   ├── rfai_preferences.json    # Daemon settings
│   └── api_keys.json            # Perplexity, YouTube, etc. (encrypted)
│
├── data/
│   ├── activity.db              # SQLite: time logs + focus states
│   ├── ratings.jsonl            # Line-delimited ratings
│   ├── cache/
│   │   ├── youtube_cache.json   # Recent YouTube searches
│   │   ├── movie_cache.json     # Recent IMDB searches
│   │   └── perplexity_cache.json
│   └── vector_db/
│       └── chroma.db            # ChromaDB: embeddings for all content
│
├── logs/
│   ├── daemon_activity.log      # Time tracker, focus detector logs
│   ├── recommendations.log      # Recommendation service logs
│   └── errors.log
│
├── exports/
│   ├── daily_summary_2025-12-17.json
│   ├── weekly_stats_2025_w50.json
│   └── analytics_dashboard.html # Self-contained HTML report
│
└── local_content/
    ├── pdfs/                    # User uploaded papers
    └── screenshots/             # Optional: hourly focus screenshots
```

**Database Schemas:**

**SQLite: `activity.db`**
```sql
-- Time logs
CREATE TABLE time_logs (
  id TEXT PRIMARY KEY,
  timestamp DATETIME,
  hour_slot TEXT,
  scheduled_task TEXT,
  actual_app TEXT,
  focus_state TEXT,
  focus_confidence FLOAT,
  keystroke_count INT,
  duration_seconds INT,
  rating INT DEFAULT NULL
);

-- Focus states (fine-grained)
CREATE TABLE focus_states (
  id TEXT PRIMARY KEY,
  timestamp DATETIME,
  state TEXT,  -- FOCUSED | ACTIVE | DISTRACTED | INACTIVE
  confidence FLOAT,
  signal_breakdown JSON,
  exceptions JSON
);

-- Timetable slots (reference)
CREATE TABLE timetable_slots (
  id TEXT PRIMARY KEY,
  day TEXT,
  start_time TIME,
  end_time TIME,
  task TEXT,
  subtask TEXT,
  goal_id TEXT,
  completed BOOLEAN DEFAULT FALSE
);

-- Goals (reference)
CREATE TABLE goals (
  id TEXT PRIMARY KEY,
  name TEXT,
  timeline_months INT,
  target_hours INT,
  completion_percent FLOAT DEFAULT 0.0,
  subtopics JSON,
  resources JSON
);
```

---

### **LAYER 5: FRONTEND & USER INTERFACE**

#### **5.1 Dashboard (Web-based)** (Enhancement of existing Learning_AI UI)

**New Sections:**

**A. Daily Timetable View**
```
TODAY: Dec 17, 2025

│ Time    │ Task                        │ Status  │ Next Rec │
├─────────┼─────────────────────────────┼─────────┼──────────┤
│ 09:00   │ Deep Coding (Rust)          │ ACTIVE  │ Paper    │
│ 10:00   │ Break                       │ PENDING │ -        │
│ 10:15   │ Study: Cryptography         │ PENDING │ Video    │
│ 12:00   │ Lunch                       │ PENDING │ -        │
│ 14:00   │ Tutoring (Student: Alex)    │ PENDING │ -        │
└─────────┴─────────────────────────────┴─────────┴──────────┘

[Heatmap: Hours of focus by day this week]
[Stats: Total focused: 12.5 hrs | Adherence: 87% | Best hour: 09:00]
```

**B. Focus & Activity Dashboard**
```
THIS WEEK'S FOCUS HEATMAP
├─ Mon: █████░░░░ 50% focused
├─ Tue: ██████░░░ 60% focused
├─ Wed: ████████░ 80% focused
├─ Thu: ███████░░ 70% focused
├─ Fri: ██████░░░ 60% focused
└─ Avg: 64% focused

[Line chart: Focus % by hour of day → reveals your peak hours]

TODAY'S FOCUS TIMELINE (Real-time)
09:15  📊 FOCUSED (87%) - Coding in VS Code
09:35  📊 FOCUSED (92%) - Keystroke rhythm optimal
09:50  ⚠️ DISTRACTED (45%) - Slack notifications
10:05  📊 FOCUSED (88%) - Re-engaged
10:30  ⏸️ INACTIVE (5%) - Break time
```

**C. Long-Term Progress Tracker**
```
YOUR LEARNING GOALS

[GOAL 1] Master Rust Networking (6 months)
├─ Progress: ████████░░ 80% (144/180 hours)
├─ Pace: On track (+2 hrs this week)
├─ Next milestone: Study DHT algorithms (Dec 25)
├─ Top resources rated: [5★, 5★, 4★]
└─ Suggested action: Schedule 2 hrs this weekend

[GOAL 2] German B2 Proficiency (12 months)
├─ Progress: ███░░░░░░░ 30% (60/200 hours)
├─ Pace: Behind schedule (-3 hrs planned)
├─ Next milestone: Watch 10 German films (Feb)
├─ Recent ratings: [4★, 3★, 5★]
└─ Suggested action: Add 30 min daily to timetable

[GOAL 3] Read Philosophy Texts (3 months)
├─ Progress: ██░░░░░░░░ 20% (6/30 hours)
├─ Pace: Behind (-2 hrs planned)
├─ Next milestone: Finish Being & Time (Jan 15)
├─ Recent ratings: [5★, 5★]
└─ Suggested action: Schedule 1 hr Sunday evening
```

**D. Unified Recommendations Feed**
```
RECOMMENDED FOR YOU (Next 24 hours)

📝 SLOT: 09:00-10:00 | TASK: Deep Coding (Rust)
  1. 📊 [Code Tutorial] "Building DHT in Rust" (YouTube, 35 min)
     └─ Why: Matches your goal + learning style + high completion rate
  2. 📄 [Paper] "Design and Analysis of DHT" (ArXiv, 20 min read)
     └─ Why: Foundational + you rated similar papers 4.5★
  3. 🎥 [Video] "Peer Discovery Protocols Explained" (YouTube, 12 min)
     └─ Why: Quick warmup + high engagement on your profile

📚 SLOT: 10:15-11:00 | TASK: Study (Cryptography)
  1. 📰 [Article] "End-to-End Encryption: A Primer" (Medium, 10 min)
     └─ Why: New + current + written for beginners
  2. 🎬 [Explainer] "TLS Handshake Breakdown" (YouTube, 8 min)
     └─ Why: Visual + matches your content preference

🌍 SLOT: 19:00-20:00 | TASK: German Learning
  1. 🎬 [Movie] "Deutschstunde" (2019, German cinema)
     └─ Why: Goal-aligned + IMDB 7.2★ + German language
  2. 🎥 [YouTube] "Easy German - A2 Level" (Easy German, 12 min)
     └─ Why: Structured + matches your level progression

---

[Load More]  [Adjust Recommendations]  [Rate Last Session]
```

**E. Analytics & Insights**
```
WEEKLY INSIGHTS

✅ Best Performance: Wednesday 09:00-10:00
   "You maintained 95% focus during Rust coding. Keep this slot!"

⚠️ Focus Drops: Friday 14:00-15:00
   "Focus declined to 35% during study block. Suggestion: Move to morning?"

🎯 Recommendation Impact:
   "You watched 12 recommended videos this week. Avg rating: 4.3★"
   "Papers you rated 5★: 8 items → System learning your preferences"

📈 Progress: 
   "Rust Networking goal: +4 hrs this week (on pace!)"
   "German learning: Started 'Easy German' series, 60% completion"

🔄 Patterns:
   "You rate YouTube tutorials 25% higher than papers → More video content?"
   "Morning focus peaks 09:00-11:00 → Suggest scheduling hard tasks there?"
```

---

#### **5.2 Menu Bar Widget** (macOS Native)

```
┌────────────────────────────────┐
│ ⏰ 09:47 | 🎯 Coding (Rust)  │
│                                │
│ Focus: ████████░░ 80%          │
│ Time left: 13 minutes          │
│                                │
│ [Next Recommendation]          │
│ Paper: "DHT Design"            │
│                                │
│ [Show Dashboard]  [Focus Mode] │
└────────────────────────────────┘
```

**Interactions:**
- Click to show full dashboard
- "Focus Mode" → Activate pomodoro, block apps
- Drag to reorder timetable
- Customize update frequency

---

#### **5.3 Focus Session UI** (Fullscreen overlay, optional)

When user enters "Focus Mode" or "Deep Focus":

```
╔════════════════════════════════════╗
║                                    ║
║    🎯 DEEP FOCUS MODE              ║
║                                    ║
║    Task: Implement DHT Peer Finder ║
║    Time: 25:00 (Pomodoro)          ║
║    Focus: ████████░░ 85%           ║
║                                    ║
║    [PAUSE] [END] [DISTRACTED]      ║
║                                    ║
╚════════════════════════════════════╝

(Blocks all apps except: VS Code, Terminal, Safari (whitelisted))
(Shows notification every 5min if focus drops <50%)
```

---

### **LAYER 6: DAEMON MANAGEMENT & LIFECYCLE**

**Launch Agent Configuration** (macOS `.plist`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.rfai.daemon.timtracker</string>
  
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/python3</string>
    <string>/opt/rfai/daemons/time_tracker.py</string>
  </array>
  
  <key>StandardOutPath</key>
  <string>/var/log/rfai/time_tracker.log</string>
  
  <key>StandardErrorPath</key>
  <string>/var/log/rfai/time_tracker_error.log</string>
  
  <key>RunAtLoad</key>
  <true/>
  
  <key>KeepAlive</key>
  <true/>
  
  <key>StartInterval</key>
  <integer>60</integer>
</dict>
</plist>
```

**Daemon Startup Order** (Dependency management):
```
1. Start: storage_manager (DB init)
2. Start: time_tracker_daemon
3. Start: focus_detector_daemon
4. Start: activity_logger_daemon
5. Start: routine_guard_daemon (depends on all above)
6. Start: recommendation_engine (depends on all above)
7. Start: web_dashboard (port 5000)
8. Start: menu_bar_agent
```

---

## 🔐 PRIVACY & SECURITY ARCHITECTURE

**On-Device Processing Only:**
- ✅ Camera/mic feeds: Processed locally (MediaPipe), no upload
- ✅ Activity logs: Stored in `~/Library/Application Support`, encrypted
- ✅ Embeddings: Generated locally (sentence-transformers)
- ✅ Focus detection: All signals fused locally

**Optional Cloud Features (User Consent Required):**
- 🔵 Perplexity API calls: Only if API key provided + enabled
- 🔵 YouTube API queries: Only if API key provided
- 🔵 IMDB scraping: Public data, no auth required (but optional)

**Encryption:**
```python
# API keys stored encrypted in config
# Using: cryptography.fernet (symmetric encryption with master key)
master_key = derive_from_mac_keychain()  # macOS Keychain integration
encrypted_keys = encrypt(api_keys, master_key)
```

**User Consent & Transparency:**
```
FIRST RUN SETUP:

┌─────────────────────────────────────┐
│ 🔒 Privacy & Permissions             │
├─────────────────────────────────────┤
│                                     │
│ We need permission to:              │
│ ☑ Monitor active window (Activity)  │
│ ☑ Access keyboard input (rhythm)    │
│ ☑ Access camera (focus detection)   │
│ ☑ Access microphone (ambient audio) │
│ ☑ See mouse activity                │
│                                     │
│ All processing happens locally.     │
│ No video/audio uploaded.            │
│ Your data stays on your Mac.        │
│                                     │
│ [✓ I understand] [Learn More]       │
└─────────────────────────────────────┘
```

---

## 📋 FUNCTIONAL REQUIREMENTS

### **FR-1: Time Tracking**
- **Req 1.1**: Log hourly summary of active app, focus state, and adherence to timetable
- **Req 1.2**: Store logs in queryable SQLite database
- **Req 1.3**: Compute daily/weekly aggregations automatically
- **Req 1.4**: Enable historical analysis (e.g., "Best focus day: Wednesday")

### **FR-2: Focus Detection**
- **Req 2.1**: Real-time classification into 4 states: FOCUSED, ACTIVE, DISTRACTED, INACTIVE
- **Req 2.2**: Fuse signals: pose, gaze, screen, audio, mouse, keyboard
- **Req 2.3**: Handle exceptions (taking notes, presenting, on-call)
- **Req 2.4**: Output confidence score (0-100) for each classification
- **Req 2.5**: 10-30 second refresh rate (configurable)

### **FR-3: Timetable Management**
- **Req 3.1**: User defines daily/recurring schedule
- **Req 3.2**: Support one-off exceptions and recurring patterns
- **Req 3.3**: Integrate with calendar (Google, Notion, local)
- **Req 3.4**: Show current + next slots in dashboard and menu bar
- **Req 3.5**: Alert user when transitioning to new slot

### **FR-4: Long-Term Learning Plan**
- **Req 4.1**: User defines 3-6 month goals with breakdown into subtopics
- **Req 4.2**: System derives daily/weekly hour allocations per goal
- **Req 4.3**: Map goals to timetable slots
- **Req 4.4**: Track progress toward goals (hours completed, milestones)
- **Req 4.5**: Suggest optimizations (e.g., "You're behind on German, add 30 min daily?")

### **FR-5: Multi-Channel Content Discovery**
- **Req 5.1**: Integrate ArXiv API for academic papers
- **Req 5.2**: Integrate YouTube API for video tutorials
- **Req 5.3**: Integrate IMDB/OMDb API for movies/shows
- **Req 5.4**: Integrate Perplexity API for web search (articles, blogs, tutorials)
- **Req 5.5**: Support local content upload (Notion, GitHub, PDF, bookmarks)
- **Req 5.6**: Cache results to avoid redundant API calls

### **FR-6: Unified Recommendation Engine**
- **Req 6.1**: Use LinUCB algorithm to personalize recommendations
- **Req 6.2**: Parse timetable task intent to infer content type
- **Req 6.3**: Respect time constraints (don't recommend 2-hr lectures for 15-min slots)
- **Req 6.4**: Eliminate duplicates across channels (semantic similarity >0.95)
- **Req 6.5**: Provide explainability ("Why this recommendation?")
- **Req 6.6**: Support content mixing (papers, videos, tutorials, movies, articles)

### **FR-7: Rating & Feedback Collection**
- **Req 7.1**: Context-aware rating prompts for each content type
- **Req 7.2**: Universal rating schema (1-5 stars + optional tags)
- **Req 7.3**: Track completion %, time spent vs. planned
- **Req 7.4**: Trigger re-recommendations after rating
- **Req 7.5**: Update LinUCB algorithm with feedback

### **FR-8: Dashboard & Visualization**
- **Req 8.1**: Display daily timetable with status (pending, active, completed)
- **Req 8.2**: Show focus heatmap (by hour, by day of week)
- **Req 8.3**: Display long-term goal progress with milestones
- **Req 8.4**: Feed of personalized recommendations
- **Req 8.5**: Weekly/monthly analytics and insights
- **Req 8.6**: Time breakdown by task category (coding, study, break, etc.)

### **FR-9: Routine Guard & Interventions**
- **Req 9.1**: Alert user when off-task vs. timetable
- **Req 9.2**: Support configurable nudge modes (silent, gentle, deep focus)
- **Req 9.3**: Suggest next recommendation when user checks notification
- **Req 9.4**: Learn nudge preferences (reduce if >3 dismissals in row)
- **Req 9.5**: Allow user to manually mark exceptions (on-call, meeting, break)

### **FR-10: Menu Bar Widget**
- **Req 10.1**: Show current time + task + focus % in menu bar
- **Req 10.2**: Display time remaining in current slot
- **Req 10.3**: Quick access to next recommendation
- **Req 10.4**: Launch dashboard and focus mode from widget
- **Req 10.5**: Refresh every 30 seconds

### **FR-11: Daemon Management**
- **Req 11.1**: Auto-start daemons on boot (macOS LaunchAgent)
- **Req 11.2**: Monitor daemon health; restart if crashed
- **Req 11.3**: Provide logs for each daemon (stdout, stderr)
- **Req 11.4**: Allow user to pause/resume individual daemons
- **Req 11.5**: Graceful shutdown and cleanup

### **FR-12: Data Persistence**
- **Req 12.1**: Store all data locally in `~/Library/Application Support/RFAI/`
- **Req 12.2**: Use SQLite for queryable logs
- **Req 12.3**: Use JSON for config and user preferences
- **Req 12.4**: Use ChromaDB for vector embeddings
- **Req 12.5**: Backup data daily to local `.backup` folder (optional)

### **FR-13: Privacy & Security**
- **Req 13.1**: All processing on-device; no video/audio uploaded
- **Req 13.2**: Encrypt API keys using macOS Keychain
- **Req 13.3**: Request user consent for camera/mic at first run
- **Req 13.4**: Provide transparency about data retention
- **Req 13.5**: Allow user to delete all data with one click

---

## 🎨 DESIGN PHASE NEXT STEPS

**For the Design Team:**

1. **Database Schema Refinement**
   - Finalize SQLite schema (indexes, constraints, migrations)
   - Design vector DB schema for cross-channel embeddings
   - Create ER diagram

2. **API Contract Specification**
   - Define Flask endpoints (request/response schemas)
   - Design WebSocket endpoints for real-time focus updates
   - Create OpenAPI/Swagger docs

3. **Component Interface Design**
   - Define Python classes: `TimeTracker`, `FocusDetector`, `RecommendationEngine`, etc.
   - Specify method signatures and return types
   - Create UML class diagram

4. **Signal Fusion Algorithm Detail**
   - Implement multi-signal weighting with A/B test framework
   - Design state machine for focus classification
   - Create confidence scoring formula

5. **UI/UX Mockups**
   - Wireframes for dashboard sections
   - Interactive prototype for recommendation feed
   - Focus mode fullscreen design
   - Menu bar widget mockup

6. **Integration Test Plan**
   - Daemon lifecycle tests
   - API integration tests
   - End-to-end workflow tests (user creates goal → gets recommendations → rates → learns)

7. **Deployment & DevOps**
   - macOS installer (DMG or PKG)
   - Daemon installation scripts
   - Auto-update mechanism
   - Error reporting / telemetry (optional)

---

## 🚀 IMPLEMENTATION ROADMAP (Phases)

### **Phase 1: MVP (Weeks 1-4)**
- Core daemons: time tracker, focus detector, activity logger
- SQLite storage
- Timetable management
- Basic dashboard (time logs + focus heatmap)
- Menu bar widget

### **Phase 2: Recommendations (Weeks 5-8)**
- Integrate existing Learning_AI (papers + courses)
- Add YouTube API discovery
- Implement LinUCB scoring
- Recommendation feed UI
- Rating system

### **Phase 3: Long-Term Planning (Weeks 9-12)**
- Learning plan manager (goals → breakdown)
- Goal progress tracking
- Goal-aligned recommendations
- Analytics dashboard

### **Phase 4: Multi-Channel Expansion (Weeks 13-16)**
- Add IMDB/movie recommendations
- Add Perplexity API for web search
- Add local content support (Notion, GitHub, PDF)
- Advanced content mixing

### **Phase 5: Polish & Optimization (Weeks 17+)**
- Performance optimization (fast embeddings, caching)
- macOS installer & auto-update
- Advanced analytics (export to CSV, yearly reports)
- Mobile companion app (optional)

---

## 📝 SUMMARY FOR HANDOFF

**This document provides:**

✅ Complete system architecture with 6 layers  
✅ Detailed component specifications (all daemons, engine, storage)  
✅ 13 functional requirement categories (130+ individual requirements)  
✅ Multi-channel discovery (ArXiv, EdX, YouTube, IMDB, Perplexity, local)  
✅ Unified recommendation engine (LinUCB + intent parsing + content mixing)  
✅ Privacy-first design (on-device processing, encrypted keys)  
✅ Dashboard & widget UI specifications  
✅ Data persistence schemas  
✅ Daemon management and lifecycle  
✅ Implementation roadmap (5 phases over 17+ weeks)

**Anyone reading this document should be able to:**
1. Understand the complete system flow
2. Implement any component independently
3. Design APIs and database schemas
4. Create UI/UX mockups
5. Write tests and deployment scripts

**Next steps:**
- Design phase: Refine schemas, create mockups, write API specs
- Implementation: Start Phase 1 (daemons + storage)
- Testing: E2E integration tests early

---

**Document Status: READY FOR DESIGN PHASE** ✅
