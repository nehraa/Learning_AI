-- ============================================
-- RFAI Complete Database Schema (SQLite)
-- Routine Focus AI - Learning Management System
-- ============================================

-- Core Activity Tracking
-- ============================================

CREATE TABLE IF NOT EXISTS time_logs (
  id TEXT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  hour_slot TEXT,  -- "09:00-10:00"
  scheduled_task TEXT,
  actual_app TEXT,
  actual_urls TEXT,  -- JSON array
  files_modified TEXT,  -- JSON array
  page_title TEXT,  -- Currently viewed page/document title
  page_info_json TEXT,  -- JSON: {page_title, domain, app, url}
  focus_state TEXT,  -- FOCUSED|ACTIVE|DISTRACTED|INACTIVE
  focus_confidence REAL,
  duration_seconds INTEGER,
  keystroke_count INTEGER DEFAULT 0,
  mouse_movements INTEGER DEFAULT 0,
  rating INTEGER DEFAULT NULL,
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS focus_states (
  id TEXT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  state TEXT NOT NULL,  -- FOCUSED|ACTIVE|DISTRACTED|INACTIVE
  confidence REAL,
  signal_breakdown TEXT,  -- JSON: {pose, gaze, screen, audio, mouse, keyboard}
  exceptions TEXT,  -- JSON: ["is_taking_notes", "is_presenting"]
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_screenshots (
  id TEXT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  filepath TEXT,
  ocr_text TEXT,  -- Extracted text from screenshot
  detected_apps TEXT,  -- JSON array
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Timetable & Planning
-- ============================================

CREATE TABLE IF NOT EXISTS timetable_slots (
  id TEXT PRIMARY KEY,
  day TEXT,  -- "weekday" | "monday" | "2025-12-17"
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  task TEXT NOT NULL,
  subtask TEXT,
  goal_id TEXT,
  context TEXT,
  min_focus_target INTEGER DEFAULT 70,
  recommended_content_type TEXT,
  blocklist_apps TEXT,  -- JSON array
  notes TEXT,
  completed BOOLEAN DEFAULT FALSE,
  actual_completion_percent REAL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS goals (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  timeline_months INTEGER,
  target_hours REAL,
  completion_percent REAL DEFAULT 0.0,
  subtopics TEXT,  -- JSON array
  resources TEXT,  -- JSON object
  status TEXT DEFAULT 'active',  -- active|paused|completed
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_plans (
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

CREATE TABLE IF NOT EXISTS plan_days (
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
  actual_time_spent INTEGER DEFAULT 0,  -- seconds
  difficulty_rating INTEGER,  -- 1-5
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plan_id) REFERENCES learning_plans(id) ON DELETE CASCADE
);

-- Content & Recommendations
-- ============================================

CREATE TABLE IF NOT EXISTS content_items (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,  -- paper|video|article|book|tutorial|movie|course
  title TEXT,
  url TEXT,
  source TEXT,  -- arxiv|youtube|github|notion|local|edx
  author TEXT,
  published_date DATE,
  duration_seconds INTEGER,
  difficulty TEXT,  -- easy|medium|hard
  tags TEXT,  -- JSON array
  embedding BLOB,  -- 384-dim vector
  metadata TEXT,  -- JSON
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ratings (
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
  FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS content_digests (
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
  FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE CASCADE
);

-- Spaced Repetition System
-- ============================================

CREATE TABLE IF NOT EXISTS flashcards (
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
  next_review_date DATE,
  FOREIGN KEY (source_content_id) REFERENCES content_items(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS review_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  flashcard_id TEXT NOT NULL,
  timestamp DATETIME NOT NULL,
  response_quality INTEGER,  -- 0-5
  response_time_seconds REAL,
  confidence_level INTEGER,  -- 1-5
  FOREIGN KEY (flashcard_id) REFERENCES flashcards(id) ON DELETE CASCADE
);

-- Quizzes
-- ============================================

CREATE TABLE IF NOT EXISTS quizzes (
  id TEXT PRIMARY KEY,
  type TEXT,  -- daily_mini|weekly_comprehensive|monthly
  week_number INTEGER,
  day_number INTEGER,
  plan_id TEXT,
  questions TEXT,  -- JSON array
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plan_id) REFERENCES learning_plans(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS quiz_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quiz_id TEXT NOT NULL,
  timestamp DATETIME NOT NULL,
  score REAL,  -- 0-100
  total_questions INTEGER,
  correct_answers INTEGER,
  time_taken_seconds INTEGER,
  answers TEXT,  -- JSON: question → user_answer
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Reinforcement Learning (Pace Learning)
-- ============================================

CREATE TABLE IF NOT EXISTS rl_experiences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME NOT NULL,
  state TEXT,  -- JSON serialized state tuple
  action TEXT,
  reward REAL,
  next_state TEXT,  -- JSON
  q_value_before REAL,
  q_value_after REAL
);

CREATE TABLE IF NOT EXISTS rl_q_table (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state_key TEXT UNIQUE,  -- Serialized state tuple
  action TEXT,
  q_value REAL,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- System Configuration
-- ============================================

CREATE TABLE IF NOT EXISTS system_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  description TEXT,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Daemon Status Tracking
-- ============================================

CREATE TABLE IF NOT EXISTS daemon_status (
  daemon_name TEXT PRIMARY KEY,
  status TEXT,  -- running|stopped|error
  last_heartbeat DATETIME,
  error_message TEXT,
  start_time DATETIME,
  restart_count INTEGER DEFAULT 0
);

-- Attention Monitoring
-- ============================================

CREATE TABLE IF NOT EXISTS attention_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  timestamp DATETIME NOT NULL,
  state TEXT NOT NULL,  -- FOCUSED|ACTIVE|DISTRACTED|INACTIVE|TAKING_BREAK
  score REAL,  -- 0-100 attention score
  confidence REAL,  -- 0-1 confidence in score
  trend REAL,  -- positive = improving, negative = declining
  signals_json TEXT,  -- JSON: {camera, microphone, keyboard, mouse, window, cpu}
  capabilities_json TEXT,  -- JSON: {camera, microphone, system}
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS time_block_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  block_name TEXT NOT NULL,  -- "Science Learning Block", "Self-Help", etc.
  block_type TEXT NOT NULL,  -- science_youtube_and_papers|self_help_youtube|artistic_movies
  start_time DATETIME NOT NULL,
  end_time DATETIME,
  goal_duration_minutes INTEGER,
  actual_duration_minutes INTEGER,
  attention_average REAL,  -- Average attention during session
  content_consumed TEXT,  -- JSON: {videos: [...], papers: [...], movies: [...]}
  session_notes TEXT,
  completed BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Time Block Access Control (Soft Lock System)
-- ============================================

CREATE TABLE IF NOT EXISTS block_access_control (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  block_name TEXT NOT NULL,
  block_type TEXT NOT NULL,
  is_active BOOLEAN DEFAULT FALSE,  -- TRUE when block time is active
  locked BOOLEAN DEFAULT FALSE,  -- TRUE when user is in active block and hasn't met goal
  required_attention_threshold REAL DEFAULT 0.7,  -- Must reach 70% attention
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  allowed_content_types TEXT,  -- JSON: ["youtube_topics", "papers"] or ["movies"] etc
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Activity During Blocks (for analytics)
-- ============================================

CREATE TABLE IF NOT EXISTS block_activity_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  timestamp DATETIME NOT NULL,
  action TEXT,  -- "content_view", "pause", "resume", "distraction_detected"
  content_type TEXT,  -- "youtube", "paper", "movie"
  page_title TEXT,
  attention_score REAL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES time_block_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS session_content_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  content_id TEXT NOT NULL,
  content_type TEXT,  -- youtube|paper|movie
  title TEXT,
  metadata_json TEXT,  -- JSON with source, duration, etc.
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES time_block_sessions(id) ON DELETE CASCADE
);

-- Indexes for Performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_time_logs_timestamp ON time_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_focus_states_timestamp ON focus_states(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_timetable_time ON timetable_slots(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_flashcards_due ON flashcards(next_review_date);
CREATE INDEX IF NOT EXISTS idx_ratings_content ON ratings(content_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_content_type ON content_items(type, difficulty);
CREATE INDEX IF NOT EXISTS idx_quiz_results_score ON quiz_results(quiz_id, score);
CREATE INDEX IF NOT EXISTS idx_plan_days_plan ON plan_days(plan_id, week_number, day_number);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);

-- Initial Configuration Data
-- ============================================

INSERT OR IGNORE INTO system_config (key, value, description) VALUES
  ('system_version', '1.0.0', 'Current system version'),
  ('first_run', 'true', 'Whether this is first run'),
  ('data_retention_days', '90', 'How long to keep activity logs'),
  ('sampling_interval_seconds', '60', 'How often to sample activity'),
  ('focus_check_interval_seconds', '30', 'How often to check focus state'),
  ('recommendation_refresh_hours', '24', 'How often to refresh recommendations');

INSERT OR IGNORE INTO daemon_status (daemon_name, status, last_heartbeat) VALUES
  ('time_tracker', 'stopped', datetime('now')),
  ('focus_detector', 'stopped', datetime('now')),
  ('attention_monitor', 'stopped', datetime('now')),
  ('activity_logger', 'stopped', datetime('now')),
  ('routine_guard', 'stopped', datetime('now'));
