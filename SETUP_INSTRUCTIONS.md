# RFAI Learning System - Setup Instructions

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional but Recommended)

The system works in **limited mode without API keys** (using sample data), but for full functionality, add your API keys to the `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

#### Required API Keys for Full Functionality:

1. **YOUTUBE_API_KEY** - Get real video recommendations
   - Get from: https://console.cloud.google.com/apis/credentials
   - Enable YouTube Data API v3
   - **FREE** (generous quota)

2. **OMDB_API_KEY** - Get movie recommendations  
   - Get from: https://www.omdbapi.com/apikey.aspx
   - **FREE** tier available (1000 requests/day)

3. **PERPLEXITY_API_KEY** - Search study materials
   - Get from: https://www.perplexity.ai/settings/api
   - Paid service (very affordable)

#### Optional API Keys:

- **NOTION_API_KEY** - Sync learning progress to Notion
- **GEMINI_API_KEY** - AI-powered summaries
- **OLLAMA** - Local LLM (no API key needed, just install Ollama)

### 3. Start the Server

```bash
# Start with full features (daemons + API)
python3 rfai_server.py --host 0.0.0.0 --port 5000

# Or start without daemons (API only)
python3 rfai_server.py --host 0.0.0.0 --port 5000 --no-daemons
```

### 4. Open the Dashboard

Navigate to: http://localhost:5000

## 📚 Features

### ✅ What Works NOW (Even Without API Keys):

1. **Time Block System** - 3 configurable time blocks per day
   - Science Learning Block (09:00-12:00)
   - Self-Help & Philosophy (13:00-14:00)  
   - Movie & Reflection (18:00-19:30)

2. **Content Recommendations** (Sample Data)
   - YouTube Videos (science & self-help)
   - Research Papers (from ArXiv)
   - Artistic Movies
   - **Shows ALL content when no time block is active**
   - **Shows block-specific content during active blocks**

3. **Course Links**
   - Direct links to edX, MIT OpenCourseWare, Coursera, Khan Academy

4. **Quiz System**
   - Generate AI quizzes for any topic
   - Test your knowledge with multiple-choice questions
   - Track progress and scores

5. **Study Material Search**
   - Search with Perplexity API (when configured)
   - Get curated learning resources

6. **Notion Integration**
   - Sync your learning progress to Notion (when configured)

7. **Soft-Lock System**
   - Content access control during time blocks
   - Encourages focused learning

8. **Attention Tracking** (When daemons enabled)
   - Monitors your focus level
   - Tracks learning time
   - Provides insights

### 🎯 With API Keys, You Get:

- **Real YouTube video recommendations** based on your interests
- **Actual movie data** from OMDb/IMDb
- **Live ArXiv papers** in your fields of interest
- **Smart study material search** using Perplexity AI
- **Notion sync** for your learning progress

## 🎨 Configuration

Edit `interests.json` to customize:

1. **Your Learning Topics**
   - Science topics (Quantum Mechanics, Chemistry, etc.)
   - Self-help topics (Psychology, Philosophy, etc.)
   - Research fields
   - Preferred movie directors and genres

2. **Time Blocks**
   - Start/end times
   - Duration
   - Content types per block
   - Themes and icons

3. **Learning Goals**
   - Daily hours
   - Focus areas
   - Target completion weeks

## 📱 Dashboard Overview

The dashboard shows:

1. **Current Time Block** (if active)
   - Shows what you should be learning right now
   - Progress bar for goal completion
   - Start/End session buttons

2. **Attention Score**
   - Real-time focus monitoring (when daemons enabled)
   - Trend indicators

3. **Daily Schedule**
   - All your time blocks for the day
   - Visual indicators for active blocks

4. **Learning Resources**
   - **ALL RECOMMENDATIONS when no block is active**
   - **Block-specific content during active blocks**
   - YouTube videos, research papers, movies

5. **Soft-Lock Panel**
   - Shows current access restrictions
   - Lists allowed/blocked content types

6. **Online Courses**
   - Quick links to major MOOC platforms
   - Study material search

7. **Quiz System**
   - Generate quizzes for any topic
   - Test your understanding
   - Track results

8. **Notion Integration**
   - Sync your progress
   - One-click export

## 🔧 Troubleshooting

### No content showing?
- Check if API keys are configured in `.env`
- Without keys, you'll see sample data
- Restart server after adding keys

### Attention tracking not working?
- Make sure daemons are enabled (remove `--no-daemons` flag)
- Daemons require additional permissions for camera/screen access

### Quiz generation failing?
- Requires local LLM (Ollama) or Gemini API key
- Install Ollama for free local AI: https://ollama.ai

### Time blocks not showing correctly?
- Check timezone in `interests.json` → `daily_schedule.timezone`
- Default is "Asia/Kolkata"

## 📊 API Endpoints

Test the API directly:

- **Status**: http://localhost:5000/health
- **Current Block**: http://localhost:5000/api/schedule/current-block
- **YouTube Recs**: http://localhost:5000/api/content/youtube-recommendations
- **Paper Recs**: http://localhost:5000/api/content/paper-recommendations
- **Movie Recs**: http://localhost:5000/api/content/movie-recommendations
- **Full Schedule**: http://localhost:5000/api/schedule/full-day

## 🎓 Next Steps

1. **Customize your interests** in `interests.json`
2. **Add API keys** for real recommendations
3. **Set your schedule** to match your routine
4. **Start learning!** The system will guide you

## 💡 Tips

- Use the **manual override** to activate any time block on demand
- **Soft-lock system** helps maintain focus during learning blocks
- Add your **favorite YouTube channels** to `interests.json` for better recommendations
- Use **quiz system** after each learning session to test retention
- **Export to Notion** to track long-term progress

## 🐛 Known Issues

- Sample data is shown when API keys are missing (by design)
- Some movie posters may not load (OMDb API limitation)
- Attention tracking requires daemon mode

## 📞 Support

For issues, check:
1. Server logs in console
2. Browser console for JavaScript errors
3. `.env` file for API key configuration
4. `interests.json` for schedule configuration

---

**Enjoy your focused learning journey! 🚀**
