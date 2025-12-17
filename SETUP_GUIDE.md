# 🚀 RFAI Complete Setup Guide

## Quick Start (5 Minutes)

### 1. **Copy and Configure Environment Variables**

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and add your API keys
# Use any text editor (nano, vim, vscode, etc.)
nano .env
```

**Required API Keys:**
- `YOUTUBE_API_KEY` - Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- `PERPLEXITY_API_KEY` - Get from [Perplexity API](https://www.perplexity.ai/settings/api)
- `OMDB_API_KEY` - Get from [OMDb API](https://www.omdbapi.com/apikey.aspx)

**Optional but Recommended:**
- `NOTION_API_KEY` + `NOTION_DATABASE_ID` - For syncing plans to Notion
- `GEMINI_API_KEY` - For AI-powered content summaries

### 2. **Configure Your Learning Interests**

Edit `interests.json` to customize your learning preferences:

```json
{
  "youtube_interests": {
    "topics": ["Quantum Mechanics", "Philosophy", "Self-Help"],
    "content_style": "learning_borderline_entertainment"
  },
  "research_paper_interests": {
    "fields": ["Quantum Physics", "Neuroscience"],
    "arxiv_categories": ["quant-ph", "q-bio.NC"]
  },
  "movie_interests": {
    "style": "artistic_film_school",
    "directors": ["Andrei Tarkovsky", "Stanley Kubrick"],
    "post_viewing_review": true
  }
}
```

### 3. **Run the Application**

**On macOS/Linux:**
```bash
./run.sh
```

**On Windows:**
```bat
run.bat
```

The server will start on `http://localhost:5000`

### 4. **Open the Dashboard**

Navigate to one of these URLs:

- **Enhanced Dashboard**: http://localhost:5000/dashboard
- **Original Dashboard**: http://localhost:5000/
- **API Status**: http://localhost:5000/api/status

---

## 📚 Understanding the 3-Hour Daily Plan

RFAI implements a structured 3-hour daily learning plan:

### Time Allocation

| Block | Duration | Content Type | Description |
|-------|----------|--------------|-------------|
| **YouTube Learning** | 1 hour | Educational entertainment | Animated history, philosophy, self-help videos |
| **Research Papers** | 1 hour | Academic papers | ArXiv papers on your topics of interest |
| **Artistic Films** | 1-2 hours | Film school quality | Movies with artistic merit, not just entertainment |

### Content Filtering

**YouTube Content Classification:**
- ✅ **Educational** - Pure learning content (lectures, tutorials)
- ✅ **Learning-Borderline** - Educational entertainment (what you want)
- ❌ **Entertainment** - Pure entertainment (vlogs, reactions, gaming)

**Movie Classification:**
- ✅ **Artistic** - Film school worthy, high artistic merit
- ⚠️ **Good Generic** - Well-rated but commercial
- ❌ **Entertainment** - Pure entertainment

### Post-Movie Review

After watching a film, the system will prompt you to answer:
1. What was the central theme or message?
2. How did cinematography contribute to storytelling?
3. What techniques did the director use?
4. How does this compare to other films?
5. What did you learn?

---

## 🎯 Features Overview

### ✅ What's Working

1. **Content Discovery**
   - YouTube video search with educational filtering
   - ArXiv paper search with difficulty estimation
   - EdX course recommendations
   - IMDb artistic film recommendations

2. **Daily Scheduling**
   - Automatic 3-hour plan generation
   - Content blocks with time allocation
   - Current week/day tracking from `daily_3hr_plan.md`

3. **Dashboard Visualization**
   - Time allocation pie chart
   - Focus level over time (when tracking enabled)
   - Progress towards daily goals
   - Content recommendations with direct links

4. **Data Collection**
   - Activity logging (when daemons enabled)
   - Focus state tracking (when daemons enabled)
   - Content ratings and reviews
   - Export functionality for ML analysis

### ⏳ In Progress / Optional

1. **Attention Tracking** (Privacy-sensitive, opt-in)
   - Camera-based focus detection
   - Screen content tracking
   - Keyboard/mouse activity monitoring

2. **Adaptive Learning** (RL Models)
   - Difficulty adjustment based on performance
   - Content recommendation refinement
   - Pace optimization

3. **Notion Integration**
   - Sync learning plans to Notion
   - Track progress across platforms

---

## 🔧 Configuration Details

### Interests.json Structure

```json
{
  "user_profile": {
    "name": "your_name",
    "learning_style": "visual_and_practical",
    "daily_hours": 3
  },
  
  "youtube_interests": {
    "topics": ["Your", "Topics", "Here"],
    "preferred_channels": ["3Blue1Brown", "Kurzgesagt"],
    "content_style": "learning_borderline_entertainment",
    "exclude_keywords": ["vlog", "reaction", "gaming"]
  },
  
  "research_paper_interests": {
    "fields": ["Your research fields"],
    "arxiv_categories": ["quant-ph", "cs.LG"],
    "difficulty_level": "intermediate_to_advanced",
    "max_papers_per_day": 3
  },
  
  "movie_interests": {
    "style": "artistic_film_school",
    "directors": ["Your favorite directors"],
    "criteria": {
      "artistic_merit": "high",
      "avoid_purely_entertaining": true
    },
    "post_viewing_review": true
  },
  
  "time_allocation": {
    "total_daily_hours": 3,
    "breakdown": {
      "youtube_learning": 1.0,
      "artistic_movies": 1.5,
      "research_papers": 1.0
    }
  }
}
```

### Daily Learning Plan

The system reads from `daily_3hr_plan.md` which should follow this structure:

```markdown
## WEEK 1: Topic Name

### DAY 1 (Mon Dec 15) — Subtopic — 3 HOURS

**Learning Objectives:**
- Objective 1
- Objective 2

**Time Breakdown:**
- **0:00-0:45 (45 min)**: Activity description
- **0:45-1:45 (60 min)**: Activity description
- **1:45-2:30 (45 min)**: Activity description
- **2:30-3:00 (30 min)**: Mini-quiz

**Mini-Quiz Questions:**
1. Question 1
2. Question 2
```

---

## 🔌 API Endpoints

### Schedule & Content

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/schedule/daily` | GET | Get today's 3-hour schedule |
| `/api/schedule/current-block` | GET | Get active content block |
| `/api/content/rate` | POST | Rate a content item (1-5 stars) |
| `/api/movie/post-review` | POST | Submit post-movie review |

### Learning Plans

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/plans` | GET | List all learning plans |
| `/api/plans/generate` | POST | Generate new plan |
| `/api/plans/<id>` | GET | Get specific plan |
| `/api/plans/<id>/current-day` | GET | Get current day's plan |

### Activity & Stats

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats/daily` | GET | Get daily statistics |
| `/api/activity/today` | GET | Get today's activity logs |
| `/api/focus/current` | GET | Get current focus state |

### Discovery

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/discovery/search` | POST | Search for content by topic |

---

## 🐛 Troubleshooting

### "API Keys Not Found" Error

**Problem:** Dashboard shows "Add API keys to .env" message

**Solution:**
1. Make sure you copied `.env.example` to `.env`
2. Edit `.env` and replace all `your_*_api_key_here` with actual keys
3. Restart the server: `./run.sh`

### "Learning Plan Showing 0 Hours"

**Problem:** Dashboard shows 0 hours even with `daily_3hr_plan.md` present

**Solution:**
1. Check that `daily_3hr_plan.md` exists in the project root
2. Verify the file follows the correct format (see above)
3. Make sure the date in DAY 1 is valid
4. Restart the server

### "No Content Recommendations"

**Problem:** Schedule shows empty content blocks

**Solution:**
1. Verify API keys are correctly configured in `.env`
2. Check `interests.json` has valid topics and categories
3. Test individual integrations:
   - YouTube: `python rfai/integrations/youtube_api.py`
   - ArXiv: `python rfai/integrations/arxiv_api.py`
   - IMDb: `python rfai/integrations/imdb_api.py`

### "Focus Data Not Showing"

**Problem:** Focus chart is empty or shows no data

**Solution:**
1. Focus tracking requires daemons to be running
2. Make sure `NO_DAEMONS=1` is NOT set in `.env`
3. Daemons are platform-specific (macOS has better support)
4. Check daemon status: `curl http://localhost:5000/api/status`

---

## 📊 Data Export for ML Analysis

The system collects focus and activity data that you can export for ML analysis:

```bash
# Via Dashboard
# Click "Export Focus Data" button

# Via API
curl http://localhost:5000/api/activity/today > focus_data.json
```

**Data Format:**
```json
{
  "date": "2025-12-17",
  "total_time_seconds": 10800,
  "focus_time_seconds": 7200,
  "focus_percentage": 66.7,
  "logs": [
    {
      "timestamp": "2025-12-17T09:00:00",
      "focus_state": "FOCUSED",
      "duration_seconds": 3600,
      "actual_app": "Browser",
      "actual_urls": ["arxiv.org/pdf/..."]
    }
  ],
  "focus_states": [
    {
      "timestamp": "2025-12-17T09:00:00",
      "state": "FOCUSED",
      "confidence": 0.95,
      "signal_breakdown": {
        "pose": 0.9,
        "gaze": 0.95,
        "keyboard": 0.85
      }
    }
  ]
}
```

---

## 🎓 Advanced Usage

### Running Without Daemons (API Only)

```bash
NO_DAEMONS=1 ./run.sh
```

This runs only the API server without background tracking.

### Custom Database Location

```bash
export RFAI_DB_PATH="/path/to/custom/database.db"
./run.sh
```

### Enabling Debug Mode

```bash
DEBUG=1 ./run.sh
```

### Testing Individual Components

```bash
# Test YouTube integration
python rfai/integrations/youtube_api.py

# Test ArXiv integration
python rfai/integrations/arxiv_api.py

# Test EdX integration
python rfai/integrations/edx_api.py

# Test IMDb integration
python rfai/integrations/imdb_api.py

# Test content scheduler
python rfai/ai/content_scheduler.py

# Test plan parser
python rfai/ai/plan_parser.py
```

---

## 📝 Notes

- API keys are **never** logged or printed
- `.env` file is in `.gitignore` - safe from commits
- Focus/camera tracking is **opt-in** via config
- All data stays **local** on your machine
- Export data anytime for your own ML analysis

---

## 🆘 Getting Help

1. Check this guide first
2. Review error messages in terminal
3. Check `rfai.log` for detailed logs
4. Test API endpoints directly: http://localhost:5000/api/status
5. Verify API keys are valid and not expired

---

## 🎉 You're All Set!

Your RFAI system is now configured and ready to help you with your structured 3-hour daily learning plan!

**Next Steps:**
1. Open http://localhost:5000/dashboard
2. Review today's schedule
3. Start with the first content block
4. Rate content as you consume it
5. Let the system learn your preferences

**Happy Learning! 📚🚀**
