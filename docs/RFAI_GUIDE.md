# 🚀 RFAI - Routine Focus AI Complete Guide

## Overview

**Routine Focus AI (RFAI)** is a comprehensive AI-powered learning management system that combines:
- **Time tracking** and activity monitoring
- **Focus detection** using multimodal signals
- **Adaptive learning plans** with reinforcement learning
- **Personalized recommendations** using LinUCB
- **Spaced repetition system** for retention
- **Smart scheduling** with ML optimization

## 🎯 Key Features

### ✅ Already Implemented

1. **Database Layer** (Complete SQLite schema)
   - Activity tracking (time logs, focus states)
   - Learning plans (52-week structured plans)
   - Content management (papers, videos, courses)
   - Spaced repetition (flashcards, reviews)
   - Quizzes and assessments
   - Reinforcement learning (Q-learning state/actions)

2. **AI Components** (All functional)
   - **PaceLearnerRL**: Learns your optimal pace and adjusts plans
   - **PlanGeneratorAI**: Generates 52-week learning plans
   - **ContentDigestAI**: Auto-summarizes content
   - **AdaptiveSRS**: Personalized spaced repetition
   - **ScheduleOptimizer**: Finds your best learning times
   - **PlanFormatProcessor**: Handles multiple plan formats

3. **Cross-Platform Daemons** (Linux/macOS/Windows)
   - **TimeTrackerDaemon**: Logs active apps and time
   - **FocusDetectorDaemon**: Detects focus state
   - Platform detection with graceful degradation

4. **REST API** (20+ endpoints)
   - Plan generation and management
   - Goal tracking
   - Activity logs and focus states
   - SRS (flashcard reviews)
   - RL adjustments

## 📋 Quick Start

### 1. Installation

```bash
# Clone the repository
cd Learning_AI

# Install dependencies
pip install -r requirements.txt

# Optional: Install platform-specific packages
# Linux: sudo apt-get install xdotool (for window detection)
# macOS: pip install pyobjc-framework-Cocoa
# Windows: pip install pywin32
```

### 2. Initialize Database

```bash
# Initialize the database
python database/init_db.py
```

### 3. Start the Server

```bash
# Start with all features (daemons + API)
python rfai_server.py

# Or start API only (no daemons)
python rfai_server.py --no-daemons

# Custom port
python rfai_server.py --port 8080
```

### 4. Access the System

Open your browser:
- Dashboard: http://localhost:5000
- API: http://localhost:5000/api
- Health Check: http://localhost:5000/health

## 🏗️ Architecture

```
RFAI System
├── Database Layer (SQLite)
│   ├── Activity tracking
│   ├── Learning plans
│   ├── Content & recommendations
│   ├── SRS & quizzes
│   └── RL state/actions
│
├── AI Layer
│   ├── PlanGeneratorAI (52-week plans)
│   ├── PaceLearnerRL (adaptive pacing)
│   ├── ContentDigestAI (summaries)
│   ├── AdaptiveSRS (spaced repetition)
│   └── ScheduleOptimizer (ML scheduling)
│
├── Daemon Layer (Background)
│   ├── TimeTrackerDaemon
│   ├── FocusDetectorDaemon
│   ├── ActivityLoggerDaemon
│   └── RoutineGuardDaemon
│
└── API Layer (Flask)
    ├── Plan management
    ├── Goal tracking
    ├── Activity & focus
    ├── SRS & quizzes
    └── RL adjustments
```

## 📖 API Documentation

### Plan Generation

**Generate a new learning plan:**
```bash
POST /api/plans/generate
Content-Type: application/json

{
  "topic": "philosophy",
  "user_context": {
    "time_available": "3 hours/day",
    "timeline": "6 months",
    "learning_style": "balanced"
  }
}
```

**Get current day:**
```bash
GET /api/plans/{plan_id}/current-day
```

**Advance to next day:**
```bash
POST /api/plans/{plan_id}/advance
```

### Goals

**Create a goal:**
```bash
POST /api/goals
Content-Type: application/json

{
  "name": "Master Quantum Mechanics",
  "timeline_months": 6,
  "target_hours": 180,
  "subtopics": ["Linear Algebra", "Operators", "QFT"]
}
```

**List goals:**
```bash
GET /api/goals
```

### Activity & Focus

**Get today's activity:**
```bash
GET /api/activity/today
```

**Get current focus state:**
```bash
GET /api/focus/current
```

### Spaced Repetition (SRS)

**Get due flashcards:**
```bash
GET /api/srs/due-cards?max=20
```

**Submit review:**
```bash
POST /api/srs/review
Content-Type: application/json

{
  "card_id": "uuid",
  "quality": 4
}
```

### Pace Learning (RL)

**Run weekly adjustment:**
```bash
POST /api/rl/weekly-adjustment
```

### System Status

**Get system status:**
```bash
GET /api/status
```

## 🧠 AI Components Explained

### 1. Plan Generator AI

Generates comprehensive learning plans using:
- **Claude API** (if available): Intelligent, context-aware plans
- **Template-based** (fallback): Structured plans without API

Features:
- 52-week plans with daily breakdown
- Time allocation (3 hours/day by default)
- Prerequisites tracking
- Mini-quizzes and weekly reviews
- Difficulty progression

### 2. Pace Learner RL (Reinforcement Learning)

Learns your optimal learning pace using Q-learning:

**State space:**
- Average daily focus hours
- Quiz scores
- Completion rate
- Burnout indicators
- Content preferences

**Actions:**
- Maintain pace
- Slow down 20% or 50%
- Speed up 20% or 50%
- Add rest days
- Adjust difficulty

**Reward function:**
```
R = α×retention + β×completion + γ×satisfaction - δ×burnout
```

### 3. Content Digest AI

Auto-generates from content:
- TL;DR summary
- Key concepts
- Definitions
- Prerequisites
- Follow-up topics
- Flashcards
- Quiz questions

### 4. Adaptive SRS (Spaced Repetition)

Personalizes review intervals based on:
- Your forgetting curve
- Response quality
- Time to recall
- Confidence levels

Algorithm: Modified SM-2 with personalization

### 5. Schedule Optimizer

Uses ML to find your best learning times:
- Random Forest for prediction
- Features: hour, day, historical focus, activity
- Optimizes for focus % and completion

## 🔧 Configuration

### Database Location

Default: `~/.rfai/data/rfai.db`

Change with:
```bash
python rfai_server.py --db-path /path/to/custom.db
```

### Daemon Intervals

Edit in daemon constructors:
- Time Tracker: 60 seconds (logs activity)
- Focus Detector: 30 seconds (checks focus)

### API Keys

For Claude API (optional):
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Without API key, system uses template-based plan generation.

## 🌐 Platform Support

### Linux (Current Environment)
✅ Full support
- Time tracking (via xdotool or fallback)
- Focus detection (CPU, simple heuristics)
- All AI components work

Optional: Install xdotool for better window detection:
```bash
sudo apt-get install xdotool
```

### macOS
✅ Full support with additional packages
```bash
pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz
```

Features:
- Native window tracking (AppKit)
- Better focus detection
- Camera/mic support (MediaPipe)

### Windows
✅ Supported with pywin32
```bash
pip install pywin32
```

## 📊 Usage Workflow

### Daily Routine (15 minutes)

1. **Start the server** (if not already running)
2. **Check dashboard** - View today's focus and tasks
3. **Review plan** - See current day's learning objectives
4. **Get recommendations** - AI suggests content
5. **Study** - System tracks your activity automatically
6. **Review flashcards** - Due cards appear in SRS
7. **Rate content** - Help AI learn your preferences

### Weekly Review (30 minutes)

1. **Check analytics** - Focus heatmap, completion rate
2. **Take weekly quiz** - Comprehensive assessment
3. **RL adjustment** - System suggests pace changes
4. **Accept/reject** - You decide on adjustments
5. **Plan next week** - Review upcoming topics

### Monthly Optimization

1. **Review goals** - Progress toward long-term objectives
2. **Analyze patterns** - Best/worst focus times
3. **Adjust schedule** - Use Schedule Optimizer suggestions
4. **Refine content mix** - Based on ratings

## 🐛 Troubleshooting

### Database Issues

**Error: "Database not found"**
```bash
# Reinitialize
python database/init_db.py
```

**Error: "Database locked"**
- Close other connections
- Restart server

### Daemon Issues

**Daemons not tracking**
- Check daemon status: `GET /api/status`
- View logs: `tail -f rfai.log`
- Restart: Stop server (Ctrl+C) and start again

**Focus detector not working**
- Install optional packages: `psutil`, `pynput`
- Check capabilities in logs
- System works with degraded signals

### API Issues

**Port already in use**
```bash
# Use different port
python rfai_server.py --port 8080
```

**Import errors**
```bash
# Ensure all dependencies installed
pip install -r requirements.txt
```

### AI Component Issues

**Plan generation fails**
- Check if Anthropic API key is set (optional)
- System will use template-based generation
- Check logs for details

**RL not learning**
- Need 2+ weeks of data
- Check that activities are being logged
- Review reward function in code

## 📈 Data & Privacy

### Data Storage

All data stored locally:
- Location: `~/.rfai/data/`
- Database: `rfai.db` (SQLite)
- Logs: `rfai.log`

### Privacy

✅ **100% Local Processing**
- No data uploaded to cloud
- Optional: Claude API (only plan generation text)
- Camera/mic: Processed locally, never uploaded

### Data Retention

Default: 90 days for activity logs
Configure in `system_config` table

### Backup

```bash
# Backup database
cp ~/.rfai/data/rfai.db ~/.rfai/data/rfai.db.backup

# Restore
cp ~/.rfai/data/rfai.db.backup ~/.rfai/data/rfai.db
```

## 🎓 Advanced Usage

### Custom Plan Format

RFAI accepts multiple plan formats via PlanFormatProcessor:
- Detailed (full spec)
- Simple (topic → subtopic → resources)
- Natural language (parsed by AI)

### Multiple Goals

Track multiple learning goals simultaneously:
- Each with independent timeline
- Progress tracked separately
- Shared content pool

### Content Integration

RFAI integrates with existing Learning_AI:
- ArXiv papers
- EdX courses
- LinUCB recommendations

Extended sources (to be added):
- YouTube (via API)
- GitHub repos
- Local PDFs
- Notion notes

## 🚧 Future Enhancements

Planned features (not yet implemented):
- WebSocket for real-time updates
- Mobile companion app
- Voice interaction
- Advanced focus modes
- Team/study group features
- Export to CSV/PDF
- Calendar integration (Google, Notion)

## 💡 Tips for Best Results

1. **Run consistently**: Keep server running daily
2. **Be honest**: Rate content accurately
3. **Trust the RL**: Give pace learner 2-3 weeks to learn
4. **Review regularly**: Weekly quizzes are important
5. **Adjust schedule**: Use optimizer suggestions
6. **Backup data**: Weekly backups recommended

## 📞 Support & Debugging

### Logs

Check logs for errors:
```bash
tail -f rfai.log
```

### Database Queries

Inspect database directly:
```bash
sqlite3 ~/.rfai/data/rfai.db

# List tables
.tables

# Sample queries
SELECT * FROM learning_plans;
SELECT * FROM focus_states ORDER BY timestamp DESC LIMIT 10;
```

### API Testing

Use curl to test endpoints:
```bash
# Health check
curl http://localhost:5000/health

# Get status
curl http://localhost:5000/api/status

# Generate plan
curl -X POST http://localhost:5000/api/plans/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "machine learning"}'
```

## 📄 License

MIT License - Use freely for personal learning

## 🙏 Credits

Built on Learning_AI foundation with:
- Flask web framework
- ChromaDB vector database
- sentence-transformers embeddings
- ArXiv and EdX content
- LinUCB reinforcement learning

---

**Ready to start your personalized learning journey? 🚀**

Run: `python rfai_server.py`
