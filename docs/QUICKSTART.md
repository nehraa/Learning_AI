# ⚡ QUICK START GUIDE

## 30 Second Overview

```
git clone or download this folder
↓
Run: ./setup.sh (Mac/Linux) or setup.bat (Windows)
↓
Run: ./run.sh (Mac/Linux) or run.bat (Windows)  
↓
Open: http://localhost:5000
↓
Enter your interests → Get recommendations → Rate → Done!
```

## Installation (Choose One)

### 🐧 Linux / 🍎 Mac

```bash
chmod +x setup.sh
./setup.sh
./run.sh
```

### 🪟 Windows

```bash
setup.bat
run.bat
```

### Manual (All Platforms)

```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# OR
venv\Scripts\activate.bat      # Windows

pip install -r requirements.txt
python app.py
```

## ✅ You'll Know It Works When

1. Setup completes with no errors
2. See message: "Running on http://127.0.0.1:5000"
3. Browser opens dashboard automatically (or visit http://localhost:5000)
4. Can enter topics and see "Load Recommendations" button

## 📝 First Steps

1. **Enter Topics** (3-5 things you want to learn about)
   - Examples: machine learning, blockchain, neural networks

2. **Click Initialize System**
   - Wait for "✓ System configured"

3. **Click Load Recommendations**
   - First time takes 30 seconds (downloading papers)
   - You'll see 5 papers + 5 courses

4. **Rate Papers/Courses** with stars (1-5)
   - Rate what looks interesting
   - System learns your taste

5. **Click Links** to view actual papers or enroll in courses
   - Papers open in PDF viewer
   - Courses open on edX.org

## 🎯 Daily Usage

- **Run server**: `./run.sh` (or `run.bat` on Windows)
- **Open browser**: http://localhost:5000
- **Load new recommendations**: Click button
- **Rate & learn**: 10-15 minutes per day
- **Stop server**: Press Ctrl+C in terminal

## 📊 File Structure You'll See

After first run:
```
learning-system/
├── app.py                  ← Main file (don't modify)
├── index.html             ← Frontend (don't modify)
├── requirements.txt       ← Dependencies (don't modify)
├── setup.sh / setup.bat   ← Setup script
├── run.sh / run.bat       ← Run script
├── data/                  ← YOUR DATA (created automatically)
│   ├── papers/           ← Paper PDFs download here
│   ├── vector_db/        ← Embeddings
│   └── user_preferences.json ← Your ratings
└── app.log                ← Logs (debug info)
```

## 🔍 Checking Status

Open `data/user_preferences.json` to see:
- Topics you're tracking
- Papers you've rated
- Your preferences

## ⚠️ Common Issues

| Problem | Solution |
|---------|----------|
| "Port 5000 already in use" | Change port in app.py line 200 |
| "Module not found" | Run: `pip install -r requirements.txt` |
| "No venv found" | Run: `python3 -m venv venv` |
| Slow first run | Normal - downloading embedding model (300MB) |
| No internet connection | System needs internet for ArXiv |

## 💾 Dependencies Explained

Only 5 packages needed:

```
flask              - Web server to show dashboard
arxiv              - Talk to arXiv API
chromadb           - Store embeddings locally  
sentence-transformers - Convert text to embeddings
numpy              - Math calculations
```

Total: ~500MB (includes model files)

## 🚀 Next Steps

After initial setup:

1. **Add more topics** - Go back and add new interests
2. **Daily runs** - Run it every morning for new recommendations
3. **Export ratings** - Check `user_preferences.json`
4. **Adjust preferences** - Edit topics as your interests evolve

## 📖 Detailed Docs

See `README.md` for complete documentation and advanced features.

## 🆘 Need Help?

1. Check `app.log` for error messages
2. Make sure Python 3.8+ is installed
3. Verify internet connection
4. Try deleting `data/` folder and starting fresh

---

**You're ready to go! 🎉**

Your personalized learning system is running.
Enter your interests and let the AI find the perfect papers and courses for you.
