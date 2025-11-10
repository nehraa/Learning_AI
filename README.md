# 🚀 ENHANCED LEARNING CURATION SYSTEM

An AI-powered personalized learning platform that discovers research papers from ArXiv and 
recommends free EdX courses. Uses reinforcement learning (LinUCB) to learn your preferences 
and improve recommendations over time.

## 🎯 Features

✅ **ArXiv Paper Discovery** - Automatically searches and downloads relevant papers
✅ **EdX Course Recommendations** - Curated free courses from top universities
✅ **LinUCB Algorithm** - Context-aware reinforcement learning for personalization
✅ **LLM Summaries** - Automatic summaries and keyword extraction for each item
✅ **Vector Database** - ChromaDB for efficient similarity search
✅ **Beautiful Dashboard** - Modern web interface with dark/light modes
✅ **Persistent Memory** - Learns your preferences over time
✅ **Daily Automation** - Optional scheduled daily curation
✅ **100% Free** - Uses only open-source tools and free APIs

## 📋 What's Included

```
learning-system/
├── app.py                  # Main Flask backend (LinUCB + discovery)
├── index.html             # Web dashboard (HTML/CSS/JS)
├── requirements.txt       # Python dependencies
├── setup.sh / setup.bat   # Initial setup script
├── run.sh / run.bat       # Run the server
└── data/                  # Created automatically
    ├── papers/            # Downloaded PDFs
    ├── vector_db/         # ChromaDB embeddings
    └── user_preferences.json # Your ratings & preferences
```

## 🛠️ Setup (One-Time)

### Option 1: Linux/Mac
```bash
# Make setup script executable and run it
chmod +x setup.sh
./setup.sh

# Then run the server
chmod +x run.sh
./run.sh
```

### Option 2: Windows
```bash
# Run setup
setup.bat

# Then run the server
run.bat
```

### Option 3: Manual Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

## ▶️ Running the System

Once setup is complete, just run:

**Linux/Mac:**
```bash
./run.sh
```

**Windows:**
```bash
run.bat
```

**Manual:**
```bash
source venv/bin/activate  # Activate environment
python app.py             # Start server
```

## 🌐 Access the Dashboard

Open your browser and go to:
```
http://localhost:5000
```

## 🎓 First Time Setup

1. **Enter Your Interests** - Add 3-5 topics you want to learn about:
   - Example: `machine learning`, `distributed systems`, `cryptography`

2. **Get Recommendations** - Click "Load Recommendations" to:
   - Search ArXiv for papers
   - Find matching EdX courses
   - Get AI-generated summaries
   - Extract key learning points

3. **Rate & Learn** - Rate each item (1-5 stars):
   - System learns your preferences
   - Next recommendations get better
   - Ratings stored in your preferences

## 📊 How It Works

### Discovery Phase
- Searches ArXiv API for papers matching your interests
- Searches EdX database for free courses
- Downloads paper metadata

### Processing Phase
- Generates embeddings using sentence-transformers
- Stores in ChromaDB vector database
- Extracts keywords and generates summaries

### Recommendation Phase
- LinUCB algorithm ranks items based on:
  - Your past ratings
  - Item similarity to your interests
  - Exploration-exploitation balance
- Presents top 5 recommendations daily

### Learning Phase
- You rate items (1-5 stars)
- Ratings stored with timestamps
- Algorithm learns your preferences
- Next day: better recommendations

## 🧠 Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend | Flask | Lightweight, simple |
| ML Algorithm | LinUCB Bandit | Context-aware recommendations |
| Embeddings | Sentence-Transformers | Fast, accurate (80MB model) |
| Vector DB | ChromaDB | Lightweight, persistent |
| Papers | ArXiv API | Free, comprehensive |
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
