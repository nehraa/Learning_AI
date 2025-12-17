# 🚀 RFAI Learning System - Quick Start Guide

## TL;DR

```bash
# 1. Install dependencies
pip install flask flask-cors requests pytz numpy pandas scikit-learn

# 2. Start server
python3 rfai_server.py --host 0.0.0.0 --port 5000 --no-daemons

# 3. Open browser
# Navigate to: http://localhost:5000
```

**That's it!** The system works immediately with sample data. 🎉

## What You'll See Immediately

✅ **Full Dashboard** with all features visible
✅ **Movie Recommendations** - 10 curated artistic films
✅ **YouTube Videos** - Sample educational content based on your interests.json
✅ **Research Papers** - Sample papers from ArXiv
✅ **Time Block System** - 3 daily blocks (Science, Self-Help, Movies)
✅ **Course Links** - Direct access to edX, MIT, Coursera, Khan Academy
✅ **Quiz System** - Generate and take quizzes on any topic
✅ **Study Search** - Perplexity integration (when API key added)
✅ **Notion Sync** - Export learning progress (when API key added)

## Adding Real Data (Optional)

Want real recommendations instead of sample data? Just add API keys:

```bash
# Edit the .env file
nano .env

# Add your keys:
YOUTUBE_API_KEY=your_key_here
OMDB_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here

# Restart server
```

### Getting API Keys (All FREE or very cheap):

1. **YouTube API Key** (FREE - generous quota)
   - https://console.cloud.google.com/apis/credentials
   - Enable "YouTube Data API v3"

2. **OMDB API Key** (FREE - 1000 requests/day)
   - https://www.omdbapi.com/apikey.aspx

3. **Perplexity API** (Paid but affordable)
   - https://www.perplexity.ai/settings/api

## Customization

Edit `interests.json` to customize:
- Your learning topics
- YouTube channels to follow
- Movie directors you like
- Time block schedule
- Research interests

## Features

### 🎯 Time Blocks
The system divides your day into focused learning blocks:
- **09:00-12:00**: Science Learning (Quantum, Chemistry, etc.)
- **13:00-14:00**: Self-Help & Philosophy
- **18:00-19:30**: Artistic Movies

During each block, content is filtered to match the block type.

### 📚 Always-On Recommendations
- **No time block active?** → See ALL recommendations
- **Time block active?** → See block-specific content
- Content never disappears!

### 🎓 Course Integration
One-click access to:
- edX
- MIT OpenCourseWare
- Coursera
- Khan Academy

### 📝 Quiz System
- Generate quizzes for ANY topic
- Multiple difficulty levels
- Instant results and feedback

### 🔍 Study Material Search
- Powered by Perplexity AI
- Search any topic
- Get curated learning resources

### 📓 Notion Integration
- Export your progress
- Sync learning data
- Track long-term goals

## Troubleshooting

### Can't see any content?
- **This shouldn't happen!** The system shows sample data by default
- Check browser console for errors (F12)
- Restart the server

### Want real data instead of samples?
- Add API keys to `.env` file
- Restart server

### Time blocks not working?
- Check timezone in `interests.json`
- Current timezone: `Asia/Kolkata`

### Server won't start?
- Install missing dependencies: `pip install -r requirements.txt`
- Check if port 5000 is already in use

## API Endpoints

Test directly in your browser:
- Health: http://localhost:5000/health
- Current Block: http://localhost:5000/api/schedule/current-block
- YouTube: http://localhost:5000/api/content/youtube-recommendations
- Papers: http://localhost:5000/api/content/paper-recommendations
- Movies: http://localhost:5000/api/content/movie-recommendations

## Next Steps

1. ✅ Server running? Great!
2. ✅ Dashboard showing content? Perfect!
3. 📝 Customize `interests.json` with your topics
4. 🔑 Add API keys for real data (optional)
5. 🎓 Start learning!

## Pro Tips

💡 **Override time blocks manually** - Click on any block to activate it
💡 **Use quiz system** after each learning session
💡 **Export to Notion** to track long-term progress
💡 **Customize time blocks** in interests.json to match your schedule

---

**Enjoy your focused learning! 🚀**

For detailed setup instructions, see: [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)
