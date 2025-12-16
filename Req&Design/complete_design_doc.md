# ðŸ"˜ ROUTINE FOCUS AI - COMPLETE DESIGN DOCUMENT
## Personal AI Learning Companion - Single User Edition

**Version:** 3.0 Final Design  
**Date:** December 17, 2025  
**Status:** Ready for Implementation

---

## ðŸ"‹ TABLE OF CONTENTS

1. [System Architecture Overview](#architecture)
2. [Complete Component Specifications](#components)
3. [Database Schema (Complete)](#database)
4. [API Specifications](#api)
5. [Library Dependencies](#libraries)
6. [UI/UX Wireframes](#ui)
7. [Implementation Roadmap](#roadmap)
8. [Deployment Guide](#deployment)

---

<a name="architecture"></a>
## 1ï¸âƒ£ SYSTEM ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────┐
│                     RFAI COMPLETE ECOSYSTEM                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  DAEMON     │  │  AI ENGINE  │  │  STORAGE    │            │
│  │  LAYER      │  │  LAYER      │  │  LAYER      │            │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤            │
│  │ TimeTracker │  │ PlanGenAI   │  │ SQLite      │            │
│  │ FocusDetect │  │ PaceLearnerRL│  │ ChromaDB    │            │
│  │ ActLogger   │  │ SRS Engine  │  │ Redis Cache │            │
│  │ RouteGuard  │  │ ContentDigest│  │ File System │            │
│  └─────────────┘  │ SchedOptimAI │  └─────────────┘            │
│         ↓         │ LinUCB Rec   │         ↑                   │
│  ┌─────────────┐  └─────────────┘  ┌─────────────┐            │
│  │ DATA        │         ↓          │ API         │            │
│  │ COLLECTION  │←────────┴─────────→│ LAYER       │            │
│  ├─────────────┤                    ├─────────────┤            │
│  │ Camera/Mic  │                    │ Flask REST  │            │
│  │ Keyboard    │                    │ WebSocket   │            │
│  │ Mouse/App   │                    │ GraphQL     │            │
│  │ Browser     │                    └─────────────┘            │
│  │ Screenshots │                           ↓                   │
│  └─────────────┘                    ┌─────────────┐            │
│         ↓                           │ FRONTEND    │            │
│  ┌──────────────────────────────────┤  LAYER      │            │
│  │ DISCOVERY & ENRICHMENT           ├─────────────┤            │
│  ├──────────────────────────────────┤ Dashboard   │            │
│  │ ArXiv │ YouTube │ IMDB │ GitHub  │ MenuBar     │            │
│  │ Perplexity │ Notion │ Local FS   │ Focus UI    │            │
│  └──────────────────────────────────┤ Voice UI    │            │
│                                     └─────────────┘            │
└──────────────────────────────────────────────────────────────────┘
```

---

<a name="components"></a>
## 2ï¸âƒ£ COMPLETE COMPONENT SPECIFICATIONS

### A. DAEMON LAYER (Background Processes)

#### Component: `TimeTrackerDaemon`
**File:** `rfai/daemons/time_tracker.py`

**Purpose:** Log hourly activity with app focus, time spent, and focus state.

**Dependencies:**
- `pyobjc` (macOS Accessibility API)
- `sqlite3` (database)
- `schedule` (periodic tasks)

**Pseudo-code:**
```python
class TimeTrackerDaemon:
    def __init__(self, db, interval=60):
        self.db = db
        self.interval = interval  # seconds
        
    def run_forever(self):
        while True:
            # Get active window
            active_app = get_active_window()  # via Accessibility API
            
            # Get focus state
            focus = get_current_focus_state()  # from FocusDetector
            
            # Log to database
            log_activity(active_app, focus)
            
            sleep(self.interval)
            
    def get_active_window(self):
        # Use NSWorkspace to get frontmost app
        from AppKit import NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        return active_app.localizedName()
```

**Configuration:**
```yaml
# config/time_tracker.yaml
sampling_interval: 60  # seconds
log_retention_days: 90
exclude_apps:
  - "System Preferences"
  - "Activity Monitor"
```

---

#### Component: `FocusDetectorDaemon`
**File:** `rfai/daemons/focus_detector.py`

**Purpose:** Real-time focus classification using multimodal signals.

**Dependencies:**
- `mediapipe` (pose/gaze detection)
- `pyaudio` (microphone)
- `pynput` (keyboard/mouse monitoring)
- `opencv-python` (camera feed)

**Signal Fusion Algorithm:**
```python
class FocusDetectorDaemon:
    def __init__(self):
        self.weights = {
            'pose': 0.35,
            'gaze': 0.20,
            'screen': 0.15,
            'audio': 0.15,
            'mouse': 0.10,
            'keyboard': 0.05
        }
        
    def compute_focus_score(self):
        # Collect signals
        pose_score = self.pose_detector.get_stillness_score()
        gaze_score = self.gaze_detector.get_center_focus()
        screen_score = self.screen_monitor.get_window_stability()
        audio_score = self.audio_monitor.get_ambient_quietness()
        mouse_score = self.mouse_monitor.get_stillness()
        keyboard_score = self.keyboard_monitor.get_typing_rhythm()
        
        # Weighted sum
        composite_score = (
            self.weights['pose'] * pose_score +
            self.weights['gaze'] * gaze_score +
            self.weights['screen'] * screen_score +
            self.weights['audio'] * audio_score +
            self.weights['mouse'] * mouse_score +
            self.weights['keyboard'] * keyboard_score
        )
        
        # Classify
        if composite_score >= 80:
            return "FOCUSED"
        elif composite_score >= 50:
            return "ACTIVE"
        elif composite_score >= 20:
            return "DISTRACTED"
        else:
            return "INACTIVE"
```

**MediaPipe Integration:**
```python
import mediapipe as mp

class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        
    def get_stillness_score(self):
        # Capture frame from webcam
        frame = capture_webcam_frame()
        
        # Process with MediaPipe
        results = self.pose.process(frame)
        
        if results.pose_landmarks:
            # Calculate movement between frames
            movement = calculate_pose_change(
                self.prev_landmarks, 
                results.pose_landmarks
            )
            
            # Low movement = high stillness = high focus
            stillness_score = max(0, 100 - movement * 10)
            
            self.prev_landmarks = results.pose_landmarks
            return stillness_score
        
        return 50  # Default
```

---

### B. AI ENGINE LAYER

#### Component: `PlanGeneratorAI`
**File:** `rfai/ai/plan_generator.py`

**Purpose:** Generate 52-week learning plans from natural language input.

**Dependencies:**
- `anthropic` (Claude API)
- `sentence-transformers` (embeddings)
- `networkx` (prerequisite graphs)

**Main Algorithm:**
```python
class PlanGeneratorAI:
    def __init__(self, anthropic_key):
        self.client = Anthropic(api_key=anthropic_key)
        self.template_plans = self.load_template_plans()
        
    def generate_plan(
        self, 
        topic: str, 
        user_context: dict
    ) -> LearningPlan:
        """
        Main entry: topic → full 52-week plan
        
        Example:
        >>> generate_plan("philosophy", {
        ...     "time_available": "3 hours/day",
        ...     "timeline": "6 months",
        ...     "learning_style": "reading-heavy"
        ... })
        """
        
        # Step 1: Analyze topic complexity
        complexity = self.analyze_topic_complexity(topic)
        
        # Step 2: Find similar template plans
        similar_templates = self.find_similar_plans(topic)
        
        # Step 3: Generate via Claude
        prompt = self.build_generation_prompt(
            topic, user_context, complexity, similar_templates
        )
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=15000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Step 4: Parse structured output
        raw_plan = json.loads(response.content[0].text)
        
        # Step 5: Build prerequisite graph
        plan = self.structure_plan(raw_plan)
        plan.prerequisite_graph = self.build_prerequisite_graph(plan)
        
        # Step 6: Enrich with resources
        plan = self.enrich_with_resources(plan)
        
        return plan
```

**Claude Prompt Template:**
```python
def build_generation_prompt(self, topic, context, complexity, templates):
    return f"""
You are an expert curriculum designer. Generate a personalized learning plan.

TOPIC: {topic}
COMPLEXITY: {complexity['difficulty']}/10
USER CONTEXT:
- Available time: {context['time_available']}
- Timeline: {context['timeline']}
- Learning style: {context['learning_style']}
- Current knowledge: {context.get('current_knowledge', 'beginner')}

SIMILAR SUCCESSFUL PLANS (for reference):
{json.dumps(templates[:2], indent=2)}

OUTPUT FORMAT (strict JSON):
{{
  "plan_id": "uuid",
  "topic": "{topic}",
  "estimated_duration_weeks": 52,
  "daily_time_hours": 3,
  "weeks": [
    {{
      "week_number": 1,
      "theme": "Foundations of {topic}",
      "days": [
        {{
          "day_number": 1,
          "date_relative": "Week 1, Monday",
          "micro_topic": "Introduction to {topic}",
          "learning_objectives": ["obj1", "obj2"],
          "time_breakdown": {{
            "00:00-00:45": "Watch intro video",
            "00:45-01:45": "Read chapter 1",
            "01:45-02:30": "Practice problems",
            "02:30-03:00": "Mini-quiz"
          }},
          "resources": [
            {{
              "type": "video|paper|book|tutorial",
              "title": "...",
              "url": "...",
              "duration_minutes": 45,
              "difficulty": "beginner|intermediate|advanced"
            }}
          ],
          "mini_quiz": [
            {{"question": "...", "answer": "...", "difficulty": "easy"}}
          ],
          "prerequisites": ["Week 0, Day 5"],
          "estimated_difficulty": 3
        }}
      ],
      "weekly_quiz": [...],
      "capstone_project": "Build something practical"
    }}
  ],
  "prerequisite_graph": {{
    "Week 2": ["Week 1"],
    "Week 5": ["Week 2", "Week 3"]
  }},
  "milestones": [
    {{"week": 4, "achievement": "Complete foundations"}},
    {{"week": 12, "achievement": "Intermediate proficiency"}}
  ]
}}

CRITICAL REQUIREMENTS:
1. Each day must have exactly 3 hours of structured activities
2. Include mini-quizzes every day (3-5 questions)
3. Weekly comprehensive quizzes on Sundays
4. Build logical prerequisite chains (don't skip foundational topics)
5. Mix content types (videos, papers, tutorials, hands-on practice)
6. Adapt to user's learning style preference
7. Include difficulty estimates for adaptive pacing

Generate the complete 52-week plan now.
"""
```

---

#### Component: `PaceLearnerRL`
**File:** `rfai/ai/pace_learner.py`

**Purpose:** Reinforcement learning agent that adjusts plan pacing based on actual performance.

**Core Algorithm: Q-Learning**
```python
class PaceLearnerRL:
    """
    State space: (focus_hours, quiz_scores, completion_rate, burnout, content_pref)
    Action space: {maintain, slow_down, speed_up, add_rest, adjust_difficulty}
    Reward: α×retention + β×completion + γ×satisfaction - δ×burnout
    """
    
    def weekly_adjustment(self):
        # 1. Get current state from DB
        state = self.get_current_state()  # tuple
        
        # 2. Choose action (ε-greedy)
        action = self.choose_action(state)
        
        # 3. Execute action (modify plan in DB)
        changes = self.execute_action(action)
        
        # 4. Compute reward (compare week N vs N-1)
        reward = self.compute_reward(prev_state, action, state)
        
        # 5. Update Q-table: Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        self.update_q_table(prev_state, action, reward, state)
        
        # 6. Save Q-table
        self.save_q_table()
        
        return {'action': action, 'changes': changes, 'reward': reward}
```

**Reward Function:**
```python
def compute_reward(self, prev_state, action, new_state):
    # Unpack states
    _, prev_quiz, prev_completion, prev_burnout, _ = prev_state
    _, new_quiz, new_completion, new_burnout, _ = new_state
    
    # Component rewards
    retention_reward = (new_quiz - prev_quiz) / 5.0  # -1 to 1
    completion_reward = (new_completion - prev_completion) / 10.0
    
    # Get user satisfaction from ratings
    satisfaction = avg_rating_last_7_days() / 5.0  # 0 to 1
    
    # Penalties
    burnout_penalty = -1.0 if new_burnout else 0.0
    deviation_penalty = -0.3 if action in ['drastic_changes'] else 0.0
    
    # Weighted sum
    return (
        0.35 * retention_reward +
        0.25 * completion_reward +
        0.25 * satisfaction +
        0.10 * burnout_penalty +
        0.05 * deviation_penalty
    )
```

---

### C. STORAGE LAYER

<a name="database"></a>
## 3ï¸âƒ£ COMPLETE DATABASE SCHEMA

```sql
-- ============================================
-- RFAI Complete Database Schema (SQLite)
-- ============================================

-- Core Activity Tracking
-- ============================================

CREATE TABLE time_logs (
  id TEXT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  hour_slot TEXT,  -- "09:00-10:00"
  scheduled_task TEXT,
  actual_app TEXT,
  actual_urls TEXT,  -- JSON array
  files_modified TEXT,  -- JSON array
  focus_state TEXT,  -- FOCUSED|ACTIVE|DISTRACTED|INACTIVE
  focus_confidence REAL,
  duration_seconds INTEGER,
  keystroke_count INTEGER,
  mouse_movements INTEGER,
  rating INTEGER DEFAULT NULL,
  notes TEXT
);

CREATE TABLE focus_states (
  id TEXT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  state TEXT NOT NULL,  -- FOCUSED|ACTIVE|DISTRACTED|INACTIVE
  confidence REAL,
  signal_breakdown TEXT,  -- JSON: {pose, gaze, screen, audio, mouse, keyboard}
  exceptions TEXT  -- JSON: ["is_taking_notes", "is_presenting"]
);

CREATE TABLE activity_screenshots (
  id TEXT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  filepath TEXT,
  ocr_text TEXT,  -- Extracted text from screenshot
  detected_apps TEXT  -- JSON array
);

-- Timetable & Planning
-- ============================================

CREATE TABLE timetable_slots (
  id TEXT PRIMARY KEY,
  day TEXT,  -- "weekday" | "monday" | "2025-12-17"
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  task TEXT NOT NULL,
  subtask TEXT,
  goal_id TEXT,
  context TEXT,
  min_focus_target INTEGER,
  recommended_content_type TEXT,
  blocklist_apps TEXT,  -- JSON array
  notes TEXT,
  completed BOOLEAN DEFAULT FALSE,
  actual_completion_percent REAL,
  FOREIGN KEY (goal_id) REFERENCES goals(id)
);

CREATE TABLE goals (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  timeline_months INTEGER,
  target_hours REAL,
  completion_percent REAL DEFAULT 0.0,
  subtopics TEXT,  -- JSON array
  resources TEXT,  -- JSON object
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE learning_plans (
  id TEXT PRIMARY KEY,
  topic TEXT NOT NULL,
  estimated_duration_weeks INTEGER,
  daily_time_hours REAL,
  current_week INTEGER DEFAULT 1,
  current_day INTEGER DEFAULT 1,
  status TEXT DEFAULT 'active',  -- active|paused|completed
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  plan_json TEXT  -- Full JSON plan
);

CREATE TABLE plan_days (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  week_number INTEGER,
  day_number INTEGER,
  date_assigned DATE,
  micro_topic TEXT,
  learning_objectives TEXT,  -- JSON array
  time_breakdown TEXT,  -- JSON object
  resources TEXT,  -- JSON array
  mini_quiz TEXT,  -- JSON array
  completed BOOLEAN DEFAULT FALSE,
  completion_date DATETIME,
  FOREIGN KEY (plan_id) REFERENCES learning_plans(id)
);

-- Content & Recommendations
-- ============================================

CREATE TABLE content_items (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,  -- paper|video|article|book|tutorial|movie
  title TEXT,
  url TEXT,
  source TEXT,  -- arxiv|youtube|github|notion|local
  author TEXT,
  published_date DATE,
  duration_seconds INTEGER,
  difficulty TEXT,  -- easy|medium|hard
  tags TEXT,  -- JSON array
  embedding BLOB,  -- 384-dim vector
  metadata TEXT,  -- JSON
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ratings (
  id TEXT PRIMARY KEY,
  user_id TEXT DEFAULT 'default',
  content_id TEXT NOT NULL,
  rating INTEGER,  -- 1-5
  rating_confidence REAL,
  tags TEXT,  -- JSON: ["core_concept", "too_hard"]
  time_spent_seconds INTEGER,
  time_planned_seconds INTEGER,
  completion_percent REAL,
  context TEXT,  -- JSON: {timetable_slot, goal_id, mood}
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (content_id) REFERENCES content_items(id)
);

CREATE TABLE content_digests (
  id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,
  tldr TEXT,
  key_concepts TEXT,  -- JSON array
  detailed_summary TEXT,
  definitions TEXT,  -- JSON object
  prerequisites TEXT,  -- JSON array
  follow_up_topics TEXT,  -- JSON array
  applications TEXT,  -- JSON array
  quiz TEXT,  -- JSON array
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (content_id) REFERENCES content_items(id)
);

-- Spaced Repetition
-- ============================================

CREATE TABLE flashcards (
  id TEXT PRIMARY KEY,
  front TEXT NOT NULL,
  back TEXT NOT NULL,
  difficulty TEXT,  -- easy|medium|hard
  source_content_id TEXT,
  created_at DATETIME NOT NULL,
  last_reviewed DATETIME,
  review_count INTEGER DEFAULT 0,
  correct_count INTEGER DEFAULT 0,
  current_interval_days REAL DEFAULT 1.0,
  ease_factor REAL DEFAULT 2.5,
  FOREIGN KEY (source_content_id) REFERENCES content_items(id)
);

CREATE TABLE review_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  flashcard_id TEXT NOT NULL,
  timestamp DATETIME NOT NULL,
  response_quality INTEGER,  -- 0-5
  response_time_seconds REAL,
  confidence_level INTEGER,  -- 1-5
  FOREIGN KEY (flashcard_id) REFERENCES flashcards(id)
);

-- Quizzes
-- ============================================

CREATE TABLE quizzes (
  id TEXT PRIMARY KEY,
  type TEXT,  -- daily_mini|weekly_comprehensive|monthly
  week_number INTEGER,
  day_number INTEGER,
  plan_id TEXT,
  questions TEXT,  -- JSON array
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plan_id) REFERENCES learning_plans(id)
);

CREATE TABLE quiz_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quiz_id TEXT NOT NULL,
  timestamp DATETIME NOT NULL,
  score REAL,  -- 0-100
  total_questions INTEGER,
  correct_answers INTEGER,
  time_taken_seconds INTEGER,
  answers TEXT,  -- JSON: question → user_answer
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
);

-- Reinforcement Learning
-- ============================================

CREATE TABLE rl_experiences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME NOT NULL,
  state TEXT,  -- JSON serialized state tuple
  action TEXT,
  reward REAL,
  next_state TEXT,  -- JSON
  q_value_before REAL,
  q_value_after REAL
);

CREATE TABLE rl_q_table (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state_key TEXT UNIQUE,  -- Serialized state tuple
  action TEXT,
  q_value REAL,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
-- ============================================

CREATE INDEX idx_time_logs_timestamp ON time_logs(timestamp DESC);
CREATE INDEX idx_focus_states_timestamp ON focus_states(timestamp DESC);
CREATE INDEX idx_timetable_time ON timetable_slots(start_time, end_time);
CREATE INDEX idx_flashcards_due ON flashcards(last_reviewed, current_interval_days);
CREATE INDEX idx_ratings_content ON ratings(content_id, timestamp DESC);
CREATE INDEX idx_content_type ON content_items(type, difficulty);
CREATE INDEX idx_quiz_results_score ON quiz_results(quiz_id, score);
```

---

<a name="api"></a>
## 4ï¸âƒ£ API SPECIFICATIONS

### Flask REST API

**Base URL:** `http://localhost:5000/api/v1`

#### Endpoints:

**1. Plan Generation**
```http
POST /plans/generate
Content-Type: application/json

{
  "topic": "philosophy",
  "user_context": {
    "time_available": "3 hours/day",
    "timeline": "6 months",
    "learning_style": "reading-heavy",
    "current_knowledge": "beginner"
  }
}

Response 201:
{
  "plan_id": "uuid",
  "topic": "philosophy",
  "estimated_weeks": 52,
  "status": "generated",
  "preview": {
    "week_1_theme": "Foundations of Philosophy",
    "first_day_topic": "What is Philosophy?"
  }
}
```

**2. Get Current Day**
```http
GET /plans/{plan_id}/current-day

Response 200:
{
  "plan_id": "uuid",
  "week": 1,
  "day": 3,
  "micro_topic": "Socratic Method",
  "time_breakdown": {...},
  "resources": [...],
  "mini_quiz": [...]
}
```

**3. Submit Quiz**
```http
POST /quizzes/{quiz_id}/submit
Content-Type: application/json

{
  "answers": {
    "question_1": "answer_1",
    "question_2": "answer_2"
  },
  "time_taken_seconds": 300
}

Response 200:
{
  "score": 85,
  "total_questions": 5,
  "correct": 4,
  "feedback": [...]
}
```

**4. Get Recommendations**
```http
GET /recommendations?slot_id={slot_id}&limit=10

Response 200:
{
  "recommendations": [
    {
      "type": "video",
      "title": "Introduction to Phenomenology",
      "url": "...",
      "predicted_rating": 4.2,
      "reason": "Matches your learning style + high completion rate"
    }
  ]
}
```

**5. Rate Content**
```http
POST /ratings
Content-Type: application/json

{
  "content_id": "uuid",
  "rating": 5,
  "tags": ["core_concept", "save_for_later"],
  "time_spent_seconds": 2700,
  "completion_percent": 100
}

Response 201:
{
  "rating_id": "uuid",
  "updated_recommendations": true
}
```

**6. Weekly RL Adjustment**
```http
POST /rl/weekly-adjustment

Response 200:
{
  "action": "slow_down_20",
  "changes": {
    "daily_hours": "3h → 2.4h",
    "timeline_extended": "25%"
  },
  "reward": 0.45,
  "q_values": {...}
}
```

### WebSocket API (Real-time)

**Endpoint:** `ws://localhost:5000/ws`

**Messages:**

```javascript
// Client → Server: Subscribe to focus updates
{
  "type": "subscribe",
  "channel": "focus_state"
}

// Server → Client: Focus state update
{
  "type": "focus_update",
  "data": {
    "state": "FOCUSED",
    "confidence": 0.87,
    "timestamp": "2025-12-17T10:15:30Z"
  }
}

// Client → Server: Request recommendation
{
  "type": "get_recommendation",
  "slot_id": "slot_001"
}

// Server → Client: Recommendation
{
  "type": "recommendation",
  "data": {
    "content": {...},
    "reason": "..."
  }
}
```

---

<a name="libraries"></a>
## 5ï¸âƒ£ LIBRARY DEPENDENCIES

### Core Libraries

```toml
# pyproject.toml or requirements.txt

[dependencies]
# AI & ML
anthropic = "^0.8.0"  # Claude API
openai = "^1.3.0"  # Optional: GPT-4 fallback
sentence-transformers = "^2.2.0"  # Embeddings
scikit-learn = "^1.3.0"  # ML models
numpy = "^1.24.0"
pandas = "^2.0.0"

# Computer Vision & Audio
mediapipe = "^0.10.0"  # Pose/gaze detection
opencv-python = "^4.8.0"  # Camera
pyaudio = "^0.2.13"  # Microphone

# System Monitoring (macOS)
pyobjc-framework-Cocoa = "^9.2"  # macOS APIs
pyobjc-framework-Quartz = "^9.2"  # Screen capture
pynput = "^1.7.6"  # Keyboard/mouse monitoring

# Web & APIs
flask = "^3.0.0"  # REST API
flask-cors = "^4.0.0"
flask-socketio = "^5.3.0"  # WebSocket
requests = "^2.31.0"
httpx = "^0.25.0"  # Async HTTP

# Content Extraction
PyMuPDF = "^1.23.0"  # PDF parsing
youtube-transcript-api = "^0.6.0"
trafilatura = "^1.6.0"  # Web article extraction
beautifulsoup4 = "^4.12.0"

# Database & Storage
chromadb = "^0.4.0"  # Vector database
redis = "^5.0.0"  # Caching

# Utilities
schedule = "^1.2.0"  # Task scheduling
python-dotenv = "^1.0.0"  # Config
pyyaml = "^6.0.1"
python-dateutil = "^2.8.2"
networkx = "^3.1"  # Prerequisite graphs
```

---

<a name="ui"></a>
## 6ï¸âƒ£ UI/UX WIREFRAMES

### Dashboard Main View

```
┌──────────────────────────────────────────────────────────────────┐
│ RFAI Dashboard                    [🔔]  [⚙️]  [@User]  [Menu ▼] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────────────────────────────┐ │
│  │  TODAY'S PLAN  │  │  FOCUS STATUS (Real-time)              │ │
│  ├────────────────┤  ├────────────────────────────────────────┤ │
│  │ 09:00-10:00    │  │  â—ï¸ 09:47 | ðŸŽ¯ Coding (Rust)          │ │
│  │ ðŸŽ¯ Deep Coding  │  │  Focus: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–'â–' 85%              │ │
│  │ [ACTIVE] 87%   │  │  Time left: 13 min                    │ │
│  │                │  │  [Next Recommendation] [Focus Mode]   │ │
│  │ 10:00-10:15    │  └────────────────────────────────────────┘ │
│  │ â˜• Break        │                                            │
│  │ [PENDING]      │  ┌────────────────────────────────────────┐ │
│  │                │  │  RECOMMENDED FOR YOU                   │ │
│  │ 10:15-11:00    │  ├────────────────────────────────────────┤ │
│  │ ðŸ"š Study        │  │  ðŸ"Š [Video] "DHT in Rust" (35 min)   │ │
│  │ [PENDING]      │  │  Why: Matches goal + high completion  │ │
│  └────────────────┘  │  Predicted rating: 4.2â˜…               │ │
│                      │                                        │ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  THIS WEEK'S FOCUS HEATMAP                               │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │  Mon: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–'â–'â–'â–' 50%  Avg: 64%                      │ │
│  │  Tue: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–'â–'â–' 60%  Best: Wed 09:00              │ │
│  │  Wed: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–' 80%  Worst: Fri 14:00            │ │
│  │  Thu: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–'â–' 70%                               │ │
│  │  Fri: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–'â–'â–' 60%  [View Details]               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  LEARNING GOALS PROGRESS                                 │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │  [🎯 Rust Networking] 80% â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–'â–' 144/180 hrs   │ │
│  │     Pace: On track (+2 hrs this week)                    │ │
│  │     Next: DHT algorithms (Dec 25)                        │ │
│  │     [View Plan] [Adjust]                                 │ │
│  │                                                           │ │
│  │  [ðŸ‡©ðŸ‡ª German B2] 30% â–ˆâ–ˆâ–ˆâ–'â–'â–'â–'â–'â–'â–' 60/200 hrs        │ │
│  │     âš ï¸ Behind schedule (-3 hrs)                         │ │
│  │     Suggestion: Add 30 min daily                         │ │
│  │     [Adjust Schedule] [Skip]                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Create New Plan] [Weekly Review] [Analytics] [SRS Review]    │
└──────────────────────────────────────────────────────────────────┘
```

### Plan Generation Interface

```
┌──────────────────────────────────────────────────────────────────┐
│ Create Your Learning Plan                             [Close ×] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: What do you want to learn?                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Philosophy                                         [🔍]   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Step 2: Your context                                           │
│  Time available:  [3 hours/day ▼]                               │
│  Timeline:        [6 months ▼]                                  │
│  Learning style:  [â˜'] Reading  [âœ"] Videos  [âœ"] Hands-on        │
│  Current level:   [Beginner ▼]                                  │
│                                                                  │
│  Step 3: Advanced options (optional)                            │
│  [+ Add prerequisites]  [+ Set difficulty]  [+ Choose format]   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  âœ¨ AI will generate:                                       │ │
│  │  • 52-week structured plan                                 │ │
│  │  • Daily 3-hour breakdown                                  │ │
│  │  • Mini-quizzes & weekly tests                             │ │
│  │  • Curated resources (papers, videos, tutorials)           │ │
│  │  • Prerequisite learning path                              │ │
│  │  • Adaptive pacing (adjusts to YOUR speed)                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Generate Plan] (takes ~30 seconds)                            │
│                                                                  │
│  OR: [Import Existing Plan] [Use Template]                      │
└──────────────────────────────────────────────────────────────────┘
```

### Focus Mode UI (Fullscreen)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                                                                  │
│                    ðŸŽ¯ DEEP FOCUS MODE                            │
│                                                                  │
│          Task: Implement DHT Peer Discovery                      │
│          Time: 23:47 (Pomodoro)                                  │
│          Focus: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–' 92%                             │
│                                                                  │
│          [⏸ Pause] [✓ Done] [😑 Distracted]                     │
│                                                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

(Full screen overlay, blocks all apps except whitelist)
```

### Menu Bar Widget (macOS)

```
┌───────────────────────────────┐
│ â° 09:47 | ðŸŽ¯ Coding (Rust)   │
│                               │
│ Focus: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–'â–' 85%        │
│ Time left: 13 minutes         │
│                               │
│ [Next Recommendation]         │
│ Paper: "DHT Design"           │
│                               │
│ [Show Dashboard] [Focus Mode] │
└───────────────────────────────┘
```

### SRS Review Interface

```
┌──────────────────────────────────────────────────────────────────┐
│ Flashcard Review                           [Cards: 15 remaining] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                            │ │
│  │                                                            │ │
│  │           What is the Socratic Method?                     │ │
│  │                                                            │ │
│  │                                                            │ │
│  │                   [Show Answer]                            │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  (After showing answer:)                                         │
│                                                                  │
│  How well did you remember?                                      │
│  [1 - Wrong] [2 - Hard] [3 - Good] [4 - Easy] [5 - Perfect]     │
│                                                                  │
│  Confidence: [😰] [😐] [😊] [😄] [🤩]                            │
│                                                                  │
│  [⏭ Skip] [✏️ Edit Card] [🗑 Delete]                            │
└──────────────────────────────────────────────────────────────────┘
```

---

<a name="roadmap"></a>
## 7ï¸âƒ£ IMPLEMENTATION ROADMAP

### Phase 1: Core Infrastructure (Weeks 1-3)

**Week 1: Storage & Daemons**
- [ ] Set up SQLite database with complete schema
- [ ] Implement TimeTrackerDaemon (basic version)
- [ ] Implement FocusDetectorDaemon (without ML, just thresholds)
- [ ] Implement ActivityLoggerDaemon
- [ ] macOS LaunchAgent setup
- [ ] Test: Daemons run 24/7 without crashing

**Week 2: Basic Dashboard**
- [ ] Flask API server (GET /focus, GET /activity)
- [ ] React dashboard skeleton
- [ ] Display time logs table
- [ ] Display focus heatmap (Chart.js)
- [ ] Menu bar widget (simple version)
- [ ] Test: Can view today's activity

**Week 3: Timetable System**
- [ ] Timetable CRUD (Create, Read, Update, Delete)
- [ ] Recurring pattern parser ("Mon-Fri 9am-10am")
- [ ] Timetable viewer UI
- [ ] Routine Guard daemon (basic alerts)
- [ ] Test: Can create daily schedule and get nudges

---

### Phase 2: AI Plan Generation (Weeks 4-6)

**Week 4: Plan Generator Core**
- [ ] PlanGeneratorAI class
- [ ] Claude API integration
- [ ] Prompt engineering for plan generation
- [ ] Parse JSON plan output
- [ ] Store plan in database
- [ ] Test: Generate plan for "philosophy" topic

**Week 5: Plan Enrichment**
- [ ] Prerequisite graph builder (NetworkX)
- [ ] Resource discovery (ArXiv, YouTube APIs)
- [ ] Content embeddings (sentence-transformers)
- [ ] Store enriched plan
- [ ] Test: Plan has curated resources

**Week 6: Plan Execution**
- [ ] Display current day's plan
- [ ] Show time breakdown & resources
- [ ] Mini-quiz interface
- [ ] Mark day as complete
- [ ] Progress tracking
- [ ] Test: Complete Day 1 end-to-end

---

### Phase 3: RL & Adaptive Pacing (Weeks 7-9)

**Week 7: PaceLearnerRL**
- [ ] State space computation from DB
- [ ] Action execution (modify plan)
- [ ] Reward function implementation
- [ ] Q-learning update logic
- [ ] Q-table persistence
- [ ] Test: Weekly adjustment runs without errors

**Week 8: ML Models**
- [ ] Schedule Optimizer (RandomForest)
- [ ] Forgetting curve model (SRS)
- [ ] Focus quality predictor
- [ ] Train models on synthetic data
- [ ] Test: Models make reasonable predictions

**Week 9: Integration**
- [ ] Connect RL to dashboard
- [ ] Show adjustment recommendations
- [ ] User can accept/reject adjustments
- [ ] Track adjustment outcomes
- [ ] Test: System adapts to slow pace

---

### Phase 4: Content System (Weeks 10-12)

**Week 10: Multi-Channel Discovery**
- [ ] ArXiv integration
- [ ] YouTube API integration
- [ ] Perplexity API integration
- [ ] GitHub API integration
- [ ] Local file indexing
- [ ] Test: Can discover 100+ resources

**Week 11: Recommendation Engine**
- [ ] LinUCB implementation
- [ ] Context fusion algorithm
- [ ] Deduplication logic
- [ ] Ranking & scoring
- [ ] Test: Get top 10 recommendations

**Week 12: Rating & Feedback**
- [ ] Rating UI (context-aware prompts)
- [ ] Store ratings with embeddings
- [ ] Update LinUCB model
- [ ] Generate insights
- [ ] Test: System learns preferences after 20 ratings

---

### Phase 5: Advanced Features (Weeks 13-15)

**Week 13: Content Digestion**
- [ ] PDF text extraction
- [ ] YouTube transcript fetching
- [ ] Article scraping
- [ ] Claude digest generation
- [ ] Store digests
- [ ] Test: Auto-generate notes from paper

**Week 14: Spaced Repetition**
- [ ] Flashcard CRUD
- [ ] SRS scheduling algorithm
- [ ] Review interface
- [ ] Forgetting model training
- [ ] Test: Review 20 cards with adaptive intervals

**Week 15: Polish**
- [ ] Voice interaction (Whisper API)
- [ ] Focus mode fullscreen UI
- [ ] Export analytics (CSV, PDF)
- [ ] Performance optimization
- [ ] Bug fixes

---

### Phase 6: Deployment (Week 16)

- [ ] macOS installer (DMG)
- [ ] Auto-updater
- [ ] Crash reporting
- [ ] Documentation
- [ ] Tutorial video

---

<a name="deployment"></a>
## 8ï¸âƒ£ DEPLOYMENT GUIDE

### Installation (macOS)

**1. Install Dependencies:**
```bash
# Install Homebrew (if not already)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Install Redis (for caching)
brew install redis
brew services start redis

# Clone repo
git clone https://github.com/your-username/rfai.git
cd rfai

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

**2. Set Up API Keys:**
```bash
# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key  # optional
YOUTUBE_API_KEY=your_youtube_key
PERPLEXITY_API_KEY=your_perplexity_key
EOF
```

**3. Initialize Database:**
```bash
python scripts/init_database.py
```

**4. Install Daemons:**
```bash
# Install LaunchAgents
python scripts/install_daemons.py

# This will create:
# ~/Library/LaunchAgents/com.rfai.timetracker.plist
# ~/Library/LaunchAgents/com.rfai.focusdetector.plist
# ~/Library/LaunchAgents/com.rfai.activitylogger.plist
# ~/Library/LaunchAgents/com.rfai.routineguard.plist

# Start daemons
launchctl load ~/Library/LaunchAgents/com.rfai.*.plist
```

**5. Grant Permissions:**
```bash
# System Preferences → Security & Privacy → Privacy
# Grant permissions for:
# - Accessibility (window monitoring)
# - Camera (focus detection)
# - Microphone (ambient audio)
# - Screen Recording (screenshots)
```

**6. Start Dashboard:**
```bash
# Terminal 1: Start Flask API
python rfai/api/server.py

# Terminal 2: Start React dashboard
cd rfai/frontend
npm install
npm start

# Open: http://localhost:3000
```

### Directory Structure

```
rfai/
├── README.md
├── requirements.txt
├── .env
├── pyproject.toml
│
├── rfai/
│   ├── __init__.py
│   ├── config.py
│   │
│   ├── daemons/
│   │   ├── time_tracker.py
│   │   ├── focus_detector.py
│   │   ├── activity_logger.py
│   │   └── routine_guard.py
│   │
│   ├── ai/
│   │   ├── plan_generator.py
│   │   ├── pace_learner.py
│   │   ├── schedule_optimizer.py
│   │   ├── content_digest.py
│   │   ├── srs_engine.py
│   │   └── recommender.py
│   │
│   ├── api/
│   │   ├── server.py
│   │   ├── routes/
│   │   │   ├── plans.py
│   │   │   ├── recommendations.py
│   │   │   ├── ratings.py
│   │   │   ├── quizzes.py
│   │   │   └── rl.py
│   │   └── websocket.py
│   │
│   ├── database/
│   │   ├── schema.sql
│   │   ├── migrations/
│   │   └── models.py
│   │
│   └── utils/
│       ├── embeddings.py
│       ├── api_clients.py
│       └── helpers.py
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   │   ├── Dashboard.js
│   │   │   ├── PlanGenerator.js
│   │   │   ├── FocusHeatmap.js
│   │   │   ├── TimetableView.js
│   │   │   └── SRSReview.js
│   │   └── utils/
│   │       ├── api.js
│   │       └── websocket.js
│   └── public/
│
├── scripts/
│   ├── init_database.py
│   ├── install_daemons.py
│   ├── generate_test_data.py
│   └── train_models.py
│
└── tests/
    ├── test_daemons.py
    ├── test_ai.py
    ├── test_api.py
    └── test_integration.py
```

---

## ðŸŽ SUMMARY

This design document provides:

✅ **6 AI-powered systems** (Plan Generator, Pace Learner RL, Schedule Optimizer, Content Digest, SRS, Recommender)  
✅ **Complete database schema** (17 tables with indexes)  
✅ **Full API specifications** (REST + WebSocket)  
✅ **Library dependencies** (20+ packages)  
✅ **UI wireframes** (5 interfaces)  
✅ **16-week implementation roadmap**  
✅ **Deployment guide** with commands

**Key Innovations:**
1. **RL-based pacing** - learns YOUR optimal speed
2. **Auto-plan generation** - "philosophy" → 52-week plan
3. **Adaptive SRS** - personalized forgetting curve
4. **Multi-signal focus detection** - camera + audio + keyboard
5. **Content auto-digestion** - papers → flashcards

**Next Steps:**
1. Set up development environment
2. Start Phase 1 (daemons + storage)
3. Test with synthetic data
4. Iterate based on YOUR usage patterns

**Status:** READY FOR IMPLEMENTATION ðŸš€
