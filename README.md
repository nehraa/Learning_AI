# 🎓 RFAI (Routine Focus AI)

> **Your Intelligent Time-Block Learning System with Real Content & Progress Tracking**

RFAI is an AI-powered learning companion that structures your day into focused learning blocks, fetches actual educational content, and tracks your progress through quizzes and analytics.

## 🎉 What's New (v2.1)

### ✅ Real Content Fetching
- **YouTube Videos**: Actual videos from YouTube API (not just topics!)
- **Research Papers**: Real papers from ArXiv based on your interests
- **Movies**: Curated recommendations from IMDB
- **Auto-Display**: Content shows automatically on dashboard per time block

### ✅ AI-Powered Study Plans
- **Perplexity Integration**: Get personalized recommendations from your study plan
- **Smart Discovery**: AI finds best videos, papers, books for your goals
- **Context-Aware**: Recommendations adapt to your learning progress

### ✅ Progress Testing & Quizzes
- **Quiz Generation**: Create tests for any topic (Quantum Computing, ML, etc.)
- **Auto-Grading**: Instant feedback with explanations
- **Progress Tracking**: View scores, weak areas, improvement trends
- **Subject Analytics**: Track progress per topic

## ✨ Core Features

- ⏰ **Time-Block System** - 3 daily blocks: Science (3h), Self-Help (1h), Movies (1.5h)
- 🔒 **Soft-Lock Access Control** - Content restricted during active blocks for focus
- 📹 **Multimodal Attention** - Camera, mic, keyboard, mouse tracking
- 🎨 **Dynamic Themes** - Visual themes change per time block
- 📊 **Real-Time Dashboard** - Shows content, attention score, progress
- 💾 **Session Management** - Track learning sessions with analytics
- 🔒 **Privacy-First** - All data local, camera/mic optional

## 🚀 Quick Start (2 Minutes)

### 1. Configure API Keys

```bash
# Copy example configuration
cp .env.example .env

# Edit and add your API keys
nano .env
```

**Get Free API Keys:**
- [YouTube API](https://console.cloud.google.com/apis/credentials) - For video recommendations
- [Perplexity API](https://www.perplexity.ai/settings/api) - For web search
- [OMDb API](https://www.omdbapi.com/apikey.aspx) - For movie data

### 2. Customize Your Interests

Edit `interests.json` with your learning preferences:
- YouTube topics (Quantum Mechanics, Philosophy, etc.)
- Research paper fields and ArXiv categories
- Movie preferences (directors, genres, style)

### 3. Run the Application

**macOS / Linux:**
```bash
./run.sh
```

**Windows:**
```bat
run.bat
```

### 4. Open Dashboard

Navigate to: **http://localhost:5000/dashboard**

## 📖 How It Works

### Your 3-Hour Daily Learning Plan

RFAI implements a structured learning schedule based on `daily_3hr_plan.md`:

| Time Block | Duration | Content | Purpose |
|------------|----------|---------|---------|
| **YouTube** | 1 hour | Educational entertainment | Animated history, philosophy, self-help |
| **Papers** | 1 hour | Academic research | ArXiv papers on your topics |
| **Movies** | 1-2 hours | Artistic films | Film-school quality cinema |

### Content Intelligence

**YouTube Filtering:**
- ✅ Educational - Pure learning (lectures, tutorials)
- ✅ Learning-Borderline - What you want (educational entertainment)
- ❌ Entertainment - Excluded (vlogs, reactions, gaming)

**Movie Classification:**
- 🎬 Artistic - Film school worthy (Tarkovsky, Kubrick, etc.)
- ⭐ Good Generic - Well-rated commercial films
- 🚫 Pure Entertainment - Excluded

**After each movie, the system prompts you to reflect:**
- What was the central theme?
- How did cinematography enhance the story?
- What techniques stood out?
- What did you learn?

### Dashboard Features

- 📊 **Time Allocation Chart** - Visual breakdown of daily hours
- 📈 **Focus Over Time** - Track your attention levels
- ✅ **Progress Tracker** - See completion towards 3-hour goal
- 🎯 **Current Position** - Know your week and day in the plan
- 📝 **Content Recommendations** - Direct links to videos, papers, films

## 📚 Documentation

- **[Complete Setup Guide](SETUP_GUIDE.md)** - Detailed configuration and troubleshooting
- **[API Documentation](#api-endpoints)** - All available endpoints
- **[Configuration Reference](#configuration)** - Full `.env` and `interests.json` options

## 🔌 API Endpoints

### Schedule & Content
- `GET /api/schedule/daily` - Get today's 3-hour schedule
- `GET /api/schedule/current-block` - Get active content block
- `POST /api/content/rate` - Rate content (1-5 stars)
- `POST /api/movie/post-review` - Submit movie review

### Learning Plans
- `GET /api/plans` - List all plans
- `POST /api/plans/generate` - Generate new plan
- `GET /api/plans/<id>/current-day` - Get current day

### Activity & Stats
- `GET /api/stats/daily` - Daily statistics
- `GET /api/activity/today` - Activity logs
- `GET /api/focus/current` - Current focus state

## 🎯 Configuration

### Environment Variables (.env)

```bash
# Required
YOUTUBE_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
OMDB_API_KEY=your_key

# Optional
NOTION_API_KEY=your_key
GEMINI_API_KEY=your_key
OLLAMA_BASE_URL=http://localhost:11434
```

### Learning Interests (interests.json)

```json
{
  "youtube_interests": {
    "topics": ["Quantum Mechanics", "Philosophy"],
    "content_style": "learning_borderline_entertainment"
  },
  "research_paper_interests": {
    "fields": ["Physics", "Neuroscience"],
    "arxiv_categories": ["quant-ph", "q-bio.NC"]
  },
  "movie_interests": {
    "style": "artistic_film_school",
    "directors": ["Tarkovsky", "Kubrick"],
    "post_viewing_review": true
  }
}
```

## 🛠️ Advanced Options

### Disable Background Daemons

```bash
NO_DAEMONS=1 ./run.sh
```

### Custom Database Location

```bash
export RFAI_DB_PATH="/path/to/database.db"
./run.sh
```

### Enable Debug Logging

```bash
DEBUG=1 ./run.sh
```

### Export Focus Data for ML Analysis

```bash
# Via API
curl http://localhost:5000/api/activity/today > focus_data.json

# Or click "Export Focus Data" in dashboard
```

## 📊 Data Collection

RFAI collects data locally for your analysis:
- Activity logs (apps, websites, duration)
- Focus states (when daemons enabled)
- Content ratings and reviews
- Time allocation breakdown

**All data stays on your machine.** Export anytime for your own ML experiments.

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| API keys not working | Check `.env` file, restart server |
| Learning plan shows 0 hours | Verify `daily_3hr_plan.md` format |
| No content recommendations | Test API keys, check `interests.json` |
| Focus data empty | Enable daemons, check platform support |

**Full troubleshooting guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)

## 🔒 Privacy & Security

- ✅ API keys never logged or printed
- ✅ `.env` in `.gitignore` - safe from commits
- ✅ Camera/screen tracking is **opt-in**
- ✅ All data stored **locally**
- ✅ No cloud uploads without explicit config

## 📦 Dependencies

Core dependencies are listed in `requirements.txt`:
- Flask - API server
- ArXiv - Paper search
- Chart.js - Dashboard visualizations
- ChromaDB - Vector storage (for advanced features)
- Sentence Transformers - Content embeddings

## 🗂️ Project Structure

```
Learning_AI/
├── rfai/
│   ├── api/           # API server
│   ├── ai/            # AI components (scheduler, parser, RL)
│   ├── integrations/  # YouTube, ArXiv, EdX, IMDb
│   ├── ui/            # Dashboard UI
│   └── config/        # Configuration loaders
├── database/          # SQLite schema and init
├── .env.example       # API key template
├── interests.json     # User preferences
├── daily_3hr_plan.md  # 52-week learning plan
└── SETUP_GUIDE.md     # Complete setup docs
```

## 🎓 Legacy Version

The original Learning_AI demo is preserved in `legacy/learning_ai_basic/` for reference.

## 🤝 Contributing

This is a personal learning system, but suggestions are welcome! Please ensure:
- API keys remain secure
- Privacy features stay opt-in
- Documentation is updated

## 📄 License

MIT License - See [LICENSE](LICENSE) file

## 🆘 Need Help?

1. Read [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. Check `rfai.log` for errors
3. Test API endpoints: http://localhost:5000/api/status
4. Verify API keys are valid

---

**Made with 🧠 for structured, intentional learning**

<!--

# 🚀 RFAI (Routine Focus AI)

An AI-powered learning + routine system that combines:
- 3-hour daily learning plans (time-blocked)
- background time tracking + focus detection
- adaptive pacing (RL) + spaced repetition
- multi-source discovery (YouTube / web search / local LLM via Ollama)

## 🎯 Features

✅ **Daily 3-Hour Plans** - Time-blocked routines per day
✅ **Time Tracking Daemon** - Logs active app time (best on macOS with PyObjC)
✅ **Focus Detection Daemon** - Detects focus vs distraction (degrades gracefully)
✅ **Adaptive Pace (RL)** - Adjusts difficulty/pace based on outcomes
✅ **Spaced Repetition (SRS)** - Flashcards + review scheduling
✅ **Multi-Source Discovery** - YouTube + Perplexity + Notion (optional)
✅ **Local LLM (Ollama)** - Uses your local models when available

## 📋 What's Included

```
learning-system/
├── app.py                  # Main Flask backend (LinUCB + discovery)
├── index.html             # Web dashboard (HTML/CSS/JS)
├── requirements.txt       # Python dependencies
# 🚀 RFAI (Routine Focus AI)

RFAI is an AI-powered learning + routine system focused on **time-blocked daily plans**, **background tracking**, and **adaptive pacing**.

## One-command run

### macOS / Linux
```bash
./run.sh
```

### Windows
```bat
run.bat
```

`run.sh`/`run.bat` will create and use a local virtualenv if needed, initialize the database, and start the RFAI server.

## API

- Health: `GET /health`
- Status: `GET /api/status`
- Generate plan: `POST /api/plans/generate`
- List plans: `GET /api/plans`

The server prints the local URL on startup (default port is 5000, but the runner will choose another port if 5000 is already in use).

## Configuration (.env)

Create a `.env` file in the repo root. The server loads it on startup.

Canonical keys used by integrations:
- `YOUTUBE_API_KEY`
- `PERPLEXITY_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`
- `OLLAMA_BASE_URL` (optional)
- `OLLAMA_MODEL` (optional)

Shorthand keys are also accepted and normalized:
- `youtube` → `YOUTUBE_API_KEY`
- `perplexity` → `PERPLEXITY_API_KEY`
- `notion` → `NOTION_API_KEY`
- `gemini` → `GEMINI_API_KEY` (loaded for future use)

## Data storage

RFAI stores its SQLite DB under `~/.rfai/data/rfai.db`.

## Disable daemons (optional)

If you only want the API server:
```bash
NO_DAEMONS=1 ./run.sh
```

## Legacy app

The older “Learning_AI” demo app (the one that ran via `app.py`) is preserved under `legacy/learning_ai_basic/` but is no longer the default execution path.
| Courses | EdX | Curated, free access |
| LLM | Gemini (free tier) | Optional summaries |
| Frontend | HTML/CSS/JS | No dependencies needed |

## 📖 File Descriptions

### app.py (Main Backend)

Main Python file with all system logic:

```python
# Key Classes:
- VectorStore: ChromaDB vector database management
- PaperDiscovery: ArXiv searching
- CourseDiscovery: EdX course database
- LLMSummarizer: Summary and keyword extraction
- LinUCBArm / LinUCBPolicy: Reinforcement learning
- EnhancedSystem: Main orchestrator
- Flask app: Web API endpoints
```

**API Endpoints:**
- `GET /` - Dashboard HTML
- `POST /api/setup` - Initialize with topics
- `GET /api/get-recommendations` - Get personalized recommendations
- `POST /api/rate` - Rate an item (1-5)
- `GET /api/status` - Get system status

### index.html (Frontend)

Beautiful, modern web interface:
- Topic setup form
- Recommendation cards with:
  - Paper/course titles
  - AI-generated summaries
  - Key learning keywords
  - 5-star rating system
  - Direct links to papers/courses
- Real-time status tracking

### requirements.txt

All Python dependencies:
```
flask              # Web framework
arxiv              # ArXiv paper search
chromadb           # Vector database
sentence-transformers  # Embeddings
numpy              # Math operations
```

Total size: ~500MB (mostly models on first run)

## 🔧 Configuration

Edit top of `app.py` if needed:

```python
class Config:
    MAX_PAPERS_PER_SEARCH = 8      # Papers per search
    MAX_COURSES_PER_SEARCH = 5     # Courses per search
    CONTEXT_DIM = 384              # Embedding dimension
    ALPHA = 0.25                   # LinUCB exploration
```

## 💾 Your Data

Everything is stored locally in the `data/` directory:

```
data/
├── papers/                    # Downloaded PDFs (optional)
├── vector_db/                # ChromaDB embeddings
│   └── chroma.db            # SQLite database file
└── user_preferences.json     # Your topics and ratings
```

All data is yours. No cloud uploads unless you configure an LLM API.

## 🚀 Advanced Usage

### Setting Up Gemini API for Better Summaries

1. Get free API key at: https://ai.google.dev
2. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key"  # Linux/Mac
   # OR
   set GEMINI_API_KEY=your-api-key      # Windows
   ```
3. Restart app - will use Gemini instead of fallback

### Scheduling Daily Runs (Optional)

The system can run daily discovery automatically. Add to `app.py`:

```python
import schedule
import threading

def schedule_daily():
    schedule.every().day.at("09:00").do(lambda: system.daily_discovery(topics))

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

# Call after system init:
schedule_daily()
```

## 📱 Usage Workflow

### Daily Routine (10-15 minutes)

1. **Morning** - System has already discovered new items automatically
2. **Open Dashboard** - http://localhost:5000
3. **Review Recommendations** - Read summaries and keywords
4. **Rate Items** - Give 1-5 stars to each
5. **Choose to Read** - Click link to view/enroll
6. **Done** - System learns for tomorrow

### Weekly Review

- Check `data/user_preferences.json` to see your ratings
- Adjust topics if needed
- Monitor what papers/courses you actually complete

### Monthly Optimization

- Analyze which topics got highest ratings
- Consider refining your interests
- Update topics for better recommendations

## 🐛 Troubleshooting

### "Port 5000 already in use"
Another app is using port 5000. Either:
- Close the other app
- Change port in `app.py`: `app.run(port=5001)`

### "Module not found" errors
Make sure you activated the virtual environment:
```bash
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows
```

### ArXiv API timeout
Try again in a few minutes. ArXiv has rate limits.

### No courses found
Courses database is manually curated. Check topic keywords match course titles.

### Slow embedding generation (first time)
First run downloads models (384MB). Subsequent runs are instant.

## 📚 Learning Resources

- **ArXiv API**: https://arxiv.org/help/api
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Sentence-Transformers**: https://www.sbert.net/
- **LinUCB Algorithm**: Search "LinUCB Contextual Bandit"

## 🎯 Next Steps (Optional Enhancements)

1. **Add More Courses** - Edit `CourseDiscovery.courses` with more EdX courses
2. **Custom Topics** - Add your own topics dynamically
3. **Export Data** - Save your ratings as CSV
4. **Statistics** - Dashboard showing learning progress
5. **Email Notifications** - Daily digest of recommendations
6. **Mobile App** - Convert to React Native

## 💡 Tips for Best Results

✅ **Be consistent** - Rate papers every day
✅ **Be honest** - Rate what you actually like
✅ **Start broad** - Begin with general topics, narrow down
✅ **Review regularly** - Check your preferences weekly
✅ **Try different topics** - Explore edge cases
✅ **Share feedback** - Report missing courses or papers

## 📞 Support

- Check `app.log` for error details
- Verify internet connection (needed for ArXiv)
- Make sure you have 5GB free disk space

## 📄 License

MIT License - Use freely for personal use

## 🎉 You're All Set!

Your personalized learning assistant is ready. The more you use it and rate items, 
the better it gets at finding content you'll love.

**Now go forth and learn! 🚀**

---

**Questions?** Check the logs in `app.log` or review the code comments in `app.py`.

-->
