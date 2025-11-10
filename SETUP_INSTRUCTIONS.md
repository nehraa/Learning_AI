# 🔧 DETAILED SETUP INSTRUCTIONS

## 5-Minute Setup

Follow this step-by-step guide to get your system running.

## Step 1: Verify Python Installation

Check that you have Python 3.8 or higher:

```bash
python --version
# or
python3 --version
```

Expected output: `Python 3.8.x` or higher

If not installed, download from: https://www.python.org/downloads/

---

## Step 2: Choose Your Setup Method

### 🐧 Linux / 🍎 macOS

**Automatic Setup (Recommended):**

```bash
# Open terminal in the learning-system folder

# Make script executable
chmod +x setup.sh

# Run setup
./setup.sh

# When complete, run:
./run.sh
```

**Manual Setup:**

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

---

### 🪟 Windows

**Automatic Setup (Recommended):**

```bash
# Open Command Prompt (cmd.exe) or PowerShell
# Navigate to the learning-system folder

# Run setup
setup.bat

# When complete, run:
run.bat
```

**Manual Setup:**

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

---

## Step 3: Verify Installation

After setup completes, you should see no errors. Check with:

```bash
python -c "import flask; import arxiv; import chromadb; print('All packages installed!')"
```

Expected: `All packages installed!`

---

## Step 4: Start the Server

Activate your environment (if not already):

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate.bat
```

Then run:
```bash
python app.py
```

---

## Step 5: Open Dashboard

You'll see output like:
```
 * Running on http://127.0.0.1:5000
```

Open your browser and go to: **http://localhost:5000**

You should see the beautiful dashboard!

---

## Initial Configuration (One-Time)

### Enter Your Interests

1. In the dashboard, you'll see: **"Enter Your Interests"**

2. Type topics you want to learn about, one per line:
   ```
   machine learning
   distributed systems
   cryptography
   reinforcement learning
   ```

3. Click: **"Initialize System"**

4. Wait for: ✓ System configured

---

## First Recommendations

### Load Recommendations

1. Click: **"Load Recommendations"** button

2. Wait 20-30 seconds (first time: downloading papers)

3. You'll see 5-10 recommendation cards with:
   - Paper/Course title
   - Summary
   - Key learning points
   - 5-star rating system
   - Link to view

---

## Daily Usage

### Every Day (5-10 minutes)

1. **Start server** (if not running):
   ```bash
   ./run.sh              # Mac/Linux
   # OR
   run.bat               # Windows
   ```

2. **Open browser**: http://localhost:5000

3. **Click "Load Recommendations"**

4. **Review and rate** each item (1-5 stars)

5. **Click links** to view papers or enroll in courses

---

## Project Structure

After first setup, your folder looks like this:

```
learning-system/
│
├── 📄 app.py                      Main backend (DON'T MODIFY)
├── 🌐 index.html                  Frontend dashboard (DON'T MODIFY)
├── 📋 requirements.txt            Dependencies
├── 📖 README.md                   Full documentation
├── ⚡ QUICKSTART.md               Quick start guide
├── 🔧 DEPENDENCIES.md             Package explanations
│
├── 🔨 setup.sh                    Setup script (Linux/Mac)
├── 🔨 setup.bat                   Setup script (Windows)
├── ▶️ run.sh                       Run script (Linux/Mac)
├── ▶️ run.bat                      Run script (Windows)
│
├── 🗂️ data/                       YOUR DATA (created automatically)
│   ├── 📁 papers/                 Downloaded PDFs
│   ├── 📁 vector_db/              Embeddings & database
│   │   └── chroma.db             SQLite database
│   ├── 📄 user_preferences.json    Your topics & ratings
│   └── 📋 app.log                 System logs
│
└── 🐍 venv/                       Virtual environment (created automatically)
    └── ...
```

---

## Understanding the Workflow

### System Flow Diagram

```
Daily Schedule (9 AM)
        ↓
Search ArXiv papers
        ↓
Search EdX courses
        ↓
Generate embeddings
Store in ChromaDB
        ↓
LinUCB algorithm
ranks by preference
        ↓
Present 5 recommendations
on dashboard
        ↓
YOU rate items (1-5 stars)
        ↓
System learns preferences
        ↓
Next day: better recommendations
```

---

## Configuration Files

### user_preferences.json

After you start using the system, check this file:

```json
{
  "topics": ["machine learning", "cryptography"],
  "rated_items": {
    "2401.12345": 5,
    "2401.54321": 3
  },
  "preferences": {
    "machine learning": 1.2,
    "cryptography": 0.9
  },
  "read_count": 5,
  "last_updated": "2025-01-10T14:30:45.123456"
}
```

This shows:
- Topics you're tracking
- Papers you've rated and your ratings
- Learned preference weights
- Last time system ran

---

## Virtual Environment Explained

A **virtual environment** is an isolated Python setup:

```
System Python          Virtual Environment
    ├── Python 3.9        ├── Python 3.9
    ├── pip              ├── pip
    ├── (system pkgs)    ├── flask (only here)
    └── (system pkgs)    ├── arxiv (only here)
                         └── chromadb (only here)
```

**Why?** Keeps system clean, prevents conflicts between projects.

**Always activate before running:**

```bash
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate.bat  # Windows
```

Your prompt will show: `(venv) $`

---

## Checking Everything Works

After setup, verify with:

```bash
# Activate environment
source venv/bin/activate  # or activate.bat on Windows

# Test imports
python -c "
import flask
import arxiv
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
print('✓ Flask')
print('✓ ArXiv')
print('✓ ChromaDB')
print('✓ NumPy')
print('✓ Sentence-Transformers')
print('\nAll systems ready!')
"
```

---

## Common Setup Issues & Fixes

### Issue: "python: command not found"

**Cause:** Python 3 has a different name
**Fix:** Use `python3` instead of `python`:
```bash
python3 -m venv venv
python3 app.py
```

Or verify PATH:
```bash
which python3
which python
```

---

### Issue: "permission denied" on setup.sh

**Cause:** Script not executable
**Fix:**
```bash
chmod +x setup.sh
chmod +x run.sh
```

---

### Issue: "venv not found"

**Cause:** Virtual environment not created
**Fix:** Create manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Issue: "Port 5000 already in use"

**Cause:** Another app using port 5000
**Fix:** Change port in `app.py`:
```python
# Line ~198, change:
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

Then access: http://localhost:5001

---

### Issue: "No module named 'flask'"

**Cause:** Virtual environment not activated
**Fix:**
```bash
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate.bat  # Windows

python app.py  # Try again
```

---

### Issue: Very slow first run (10+ minutes)

**Cause:** Downloading embedding models
**Expected:** First run takes 1-2 minutes
**After:** Instant (models cached)

Do NOT interrupt - let it finish!

---

### Issue: "requests" module error

**Cause:** Optional dependency for LLM summaries
**Fix:** Install if needed:
```bash
pip install requests
```

Or ignore - system uses fallback summaries

---

## Updating/Reinstalling

### Full Fresh Start

```bash
# Delete old setup
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# Delete old data (CAREFUL!)
rm -rf data  # Linux/Mac
rmdir /s data  # Windows

# Reinstall
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Just Update Packages

```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
python app.py
```

---

## Next Steps

After successful setup:

1. **Read README.md** - Full documentation
2. **Enter your interests** - Start with 3-5 topics
3. **Load recommendations** - See first results
4. **Rate honestly** - System learns from you
5. **Check back daily** - For new recommendations

---

## Need Help?

### Debugging

Check the log file:
```bash
cat app.log  # Linux/Mac
type app.log  # Windows
```

Look for `ERROR` or `WARNING` lines.

### Reset Everything

```bash
# Delete data (careful - loses your ratings)
rm -rf data/

# Restart system
python app.py
```

### Internet Issues

The system needs internet to:
- Search ArXiv (fetch papers)
- Download embedding models (first time only)
- Fetch EdX course data

Local operations work offline after setup.

---

## Success Criteria

✅ **You're ready when:**
- Setup completes with no errors
- http://localhost:5000 opens in browser
- Dashboard loads (see "Get Started" panel)
- You can enter topics
- "Load Recommendations" button appears
- Papers and courses show up with ratings

🎉 **You're all set! Start learning!**

---

## Video Tutorials (If Available)

Look for video guides on:
- Setting up on Windows
- Setting up on Mac
- First recommendations walkthrough

Or create your own and share with the community!

---

## Support Resources

**Questions?** Check:
1. README.md (full documentation)
2. DEPENDENCIES.md (package explanations)
3. Code comments in app.py
4. app.log (error messages)

**Stuck?** Try:
1. Restart system: `python app.py`
2. Clear cache: `rm -rf data/vector_db/`
3. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

---

**You've got this! 🚀**

Next: Open http://localhost:5000 and start exploring!
