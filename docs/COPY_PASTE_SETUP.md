# ⚡ COPY-PASTE SETUP (Exact Commands)

## For Linux / macOS Users

### One-Command Setup:
```bash
chmod +x setup.sh && ./setup.sh && ./run.sh
```

### Step by Step:
```bash
# Make scripts executable
chmod +x setup.sh
chmod +x run.sh

# Run setup (installs everything)
./setup.sh

# Run the server
./run.sh
```

### Manual Setup:
```bash
# Create environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install
pip install -r requirements.txt

# Run
python app.py
```

---

## For Windows Users

### One-Click Setup:
```bash
setup.bat && run.bat
```

### Step by Step:
```bash
# Run setup (installs everything)
setup.bat

# When done, run server
run.bat
```

### PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### Command Prompt:
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

---

## After Setup

**In your browser, go to:**
```
http://localhost:5000
```

---

## Directory Structure Check

After setup, you should see:

```
├── app.py                  ✓ Present
├── index.html             ✓ Present
├── requirements.txt       ✓ Present
├── data/                  ✓ Created during first run
│   └── user_preferences.json ✓ Created after setup
├── venv/                  ✓ Created during setup
│   ├── bin/ (Mac/Linux)
│   └── Scripts/ (Windows)
└── app.log                ✓ Created on first run
```

---

## Verify Installation

After setup, run this to verify everything works:

```bash
# Activate environment first
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate.bat  # Windows

# Test all packages
python -c "
import flask; print('✓ Flask')
import arxiv; print('✓ ArXiv')  
import chromadb; print('✓ ChromaDB')
from sentence_transformers import SentenceTransformer; print('✓ Sentence-Transformers')
import numpy; print('✓ NumPy')
print('\n✅ All packages working!')
"
```

Expected output:
```
✓ Flask
✓ ArXiv
✓ ChromaDB
✓ Sentence-Transformers
✓ NumPy

✅ All packages working!
```

---

## Running Every Day

### Linux/Mac:
```bash
./run.sh
```

### Windows:
```bash
run.bat
```

### Manual any platform:
```bash
source venv/bin/activate  # Activate (skip if already active)
python app.py
```

---

## Stopping the Server

Press in terminal:
```
Ctrl + C
```

---

## Troubleshooting Commands

### If port 5000 is in use:
```bash
# Change port in app.py line 200
# Change: app.run(port=5000)
# To:     app.run(port=5001)

# Then run as normal
python app.py
# Now access: http://localhost:5001
```

### If module not found:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### If venv not found:
```bash
# Create new venv
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate.bat  # Windows

# Install
pip install -r requirements.txt

# Run
python app.py
```

### Check if Python is installed:
```bash
python --version
# or
python3 --version
```

If not, download from: https://www.python.org/downloads/

---

## Full Fresh Start (Delete Everything)

### Linux/Mac:
```bash
# Remove old setup
rm -rf venv
rm -rf data
rm -rf __pycache__
rm app.log

# Start fresh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Windows:
```bash
# Remove old setup
rmdir /s venv
rmdir /s data
rmdir /s __pycache__
del app.log

# Start fresh
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

---

## Timeline

| Step | Command | Time |
|------|---------|------|
| Setup | `./setup.sh` or `setup.bat` | 5 min |
| First run | `./run.sh` or `run.bat` | Instant |
| Initial discovery | Load Recommendations | 30 sec |
| Daily use | Just rate papers | 10 min |

---

## It's Working When You See:

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Then:
1. Browser opens automatically (or go to http://localhost:5000)
2. You see the dashboard
3. Can enter topics
4. Can load recommendations

---

## Default Settings

All in one place - these are ready to go:

**app.py - Config section:**
- ArXiv searches: 8 papers per topic
- EdX searches: 5 courses per topic
- LinUCB alpha: 0.25 (exploration rate)
- Embedding model: all-MiniLM-L6-v2

**No setup required - all configured for you!**

---

## ENV Variables (Optional)

If you want LLM summaries via Gemini:

### Linux/Mac:
```bash
export GEMINI_API_KEY="your-api-key-here"
python app.py
```

### Windows:
```bash
set GEMINI_API_KEY=your-api-key-here
python app.py
```

Get free Gemini API key: https://ai.google.dev

---

## Database & Data Location

All your data is here:
```
data/
├── user_preferences.json      # Topics, ratings, preferences
├── papers/                     # Downloaded PDFs
└── vector_db/
    └── chroma.db              # SQLite database
```

**Completely local - nothing uploaded anywhere!**

---

## System Requirements

Minimum:
- Python 3.8+
- 2GB RAM
- 5GB disk space
- Internet (for ArXiv searches)

Recommended:
- Python 3.10+
- 4GB+ RAM
- 10GB disk space
- Broadband internet

**GPU: NOT required - everything runs on CPU**

---

## Performance Tips

### First Run is Slow?
- Normal! Downloading embedding models (300MB)
- Only happens once - subsequent runs instant

### Slow Recommendations?
- Check internet connection
- ArXiv API sometimes slow
- Wait 10 seconds, try again

### Too Much Memory Usage?
- System uses max 500MB
- If more, restart with: `python app.py`

---

## Summary

```
┌─────────────────────────────────────────┐
│ 1. Run setup.sh / setup.bat             │
│ 2. Run run.sh / run.bat                 │
│ 3. Open http://localhost:5000           │
│ 4. Enter your interests                 │
│ 5. Click "Load Recommendations"         │
│ 6. Rate papers with stars               │
│ 7. Done! System learns for tomorrow    │
└─────────────────────────────────────────┘
```

---

**That's it! You're ready to start learning! 🚀**

If stuck: Read SETUP_INSTRUCTIONS.md or check app.log for errors
