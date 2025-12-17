# 📦 DEPENDENCIES GUIDE

## Overview

This system uses only 5 core Python packages. All are industry-standard and well-maintained.

## Core Dependencies

### 1. **Flask** (Web Framework)
```
Package: flask==3.0.0
Size: ~5MB
Purpose: Serves the web dashboard and API endpoints
Why: Lightweight, simple, perfect for small/medium apps
```

**What it does:**
- Runs the web server on http://localhost:5000
- Handles API requests (setup, recommendations, ratings)
- Serves HTML/CSS/JavaScript frontend

**Key in your code:**
```python
app = Flask(__name__)
@app.route('/api/recommendations')
def get_recommendations():
    ...
```

---

### 2. **ArXiv** (Paper Search)
```
Package: arxiv==2.1.0
Size: ~1MB
Purpose: Search and download paper metadata from arXiv
Why: Official Python API for arXiv.org (2.4M papers!)
```

**What it does:**
- Searches arXiv by keyword (machine learning, cryptography, etc.)
- Downloads paper titles, abstracts, authors, PDFs
- Handles rate limiting automatically

**Key in your code:**
```python
client = arxiv.Client()
search = arxiv.Search(query="machine learning", max_results=8)
for result in client.results(search):
    print(result.title)
```

---

### 3. **ChromaDB** (Vector Database)
```
Package: chromadb==0.5.23
Size: ~20MB
Purpose: Store and search paper embeddings locally
Why: Built-in SQLite, no server needed, fast similarity search
```

**What it does:**
- Stores embeddings (numerical vectors of papers)
- Performs fast similarity search (find related papers)
- Persistent storage - data survives restarts
- Runs entirely locally - no cloud needed

**Key in your code:**
```python
client = chromadb.PersistentClient(path="./data/vector_db")
collection = client.get_or_create_collection(name="papers")
collection.add(ids=[...], embeddings=[...], documents=[...])
results = collection.query(query_embeddings=[...], n_results=5)
```

---

### 4. **Sentence-Transformers** (Text Embeddings)
```
Package: sentence-transformers==3.3.1
Size: ~400MB (on first run - downloads models)
Purpose: Convert paper text to numerical embeddings
Why: Fast, accurate, lightweight (all-MiniLM-L6-v2 is only 80MB)
```

**What it does:**
- Converts text → vectors (numbers that capture meaning)
- "machine learning" and "ML" get similar vectors
- Enables semantic search (find papers about similar topics)

**Key in your code:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("machine learning paper title")
# embedding is a 384-dimensional vector
```

**First Run Note:** 
- Downloads ~80MB embedding model from HuggingFace
- Only happens once (cached locally)
- Subsequent runs use cached model (instant)

---

### 5. **NumPy** (Math)
```
Package: numpy==1.26.4
Size: ~30MB
Purpose: Numerical computations (matrix operations, etc.)
Why: Standard for ML/data science, needed by sentence-transformers
```

**What it does:**
- Matrix/vector math for embeddings
- Used by LinUCB algorithm
- Powers the reinforcement learning

**Key in your code:**
```python
import numpy as np
context = np.array([0.5, 0.2, 0.8, ...])  # embedding vector
mean = np.dot(theta.T, context)  # matrix multiplication
```

---

## Optional Dependencies

### **Requests** (HTTP Calls)
```
Package: requests==2.32.3
Size: ~1MB
Purpose: Make API calls (optional Gemini API for summaries)
```

Only needed if you set up Gemini API for LLM summaries.

---

### **Schedule** (Task Scheduling)
```
Package: schedule==1.2.2
Size: <1MB
Purpose: Run daily discovery automatically
```

Not enabled by default. Add to `app.py` if you want:
```python
schedule.every().day.at("09:00").do(daily_discovery)
```

---

## Installation Breakdown

### What Happens When You Run Setup

```bash
pip install -r requirements.txt
```

This command:

1. **Installs Flask** (~5MB)
   - Needed to serve dashboard
   - Immediate install

2. **Installs ArXiv** (~1MB)
   - Needed to search papers
   - Immediate install

3. **Installs ChromaDB** (~20MB)
   - Needed for vector DB
   - Creates SQLite database on first use

4. **Installs Sentence-Transformers** (~30MB package)
   - TRIGGERS download of embedding model (~80MB)
   - Downloads from HuggingFace on first run
   - Takes 1-2 minutes first time
   - Cached locally after

5. **Installs NumPy** (~30MB)
   - Math library
   - Immediate install

**Total Install Time:**
- First run: ~5 minutes (downloading models)
- Subsequent runs: instant

**Total Space Used:**
- After setup: ~500-600MB
- Mostly embedding models (one-time download)

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|------------|
| RAM | 2GB | 4GB+ |
| Disk | 1GB | 10GB |
| CPU | Any | Any |
| GPU | Not needed | Not needed |

**Everything runs on CPU - GPU not necessary!**

---

## Checking Installed Packages

After setup, verify everything installed:

```bash
# List all packages
pip list | grep -E "flask|arxiv|chromadb|sentence-transformers|numpy"

# Check Flask version
python -c "import flask; print(flask.__version__)"

# Check if models downloaded
ls -la ~/.cache/huggingface/hub/  # Linux/Mac
dir %USERPROFILE%\.cache\huggingface\hub  # Windows
```

---

## Version Pinning

All versions are pinned in `requirements.txt`:
```
flask==3.0.0                    # Exact version
sentence-transformers==3.3.1    # Exact version
```

This ensures:
- Reproducibility (same results every run)
- Stability (no breaking changes)
- Compatibility between packages

---

## Updating Packages (Optional)

To upgrade to latest versions later:

```bash
# Update all
pip install -r requirements.txt --upgrade

# Update specific package
pip install flask --upgrade
```

**Note:** This system was tested with pinned versions. Upgrade at your own risk.

---

## Troubleshooting Install Issues

### "ModuleNotFoundError: No module named 'flask'"

**Cause:** Virtual environment not activated
**Fix:** 
```bash
source venv/bin/activate  # Mac/Linux
# OR
venv\Scriptsctivate.bat  # Windows
```

### "pip: command not found"

**Cause:** Python not in PATH
**Fix:** Use full path:
```bash
python3 -m pip install -r requirements.txt
```

### "ImportError: numpy not found"

**Cause:** Incomplete installation
**Fix:** Reinstall:
```bash
pip install -r requirements.txt --force-reinstall
```

### Slow first run

**Cause:** Downloading embedding models
**Expected:** 1-2 minutes first time
**After:** Instant (cached)

### "chromadb" ImportError

**Cause:** ChromaDB version conflict
**Fix:**
```bash
pip uninstall chromadb
pip install chromadb==0.5.23
```

---

## Package Versions Explained

### Why Flask 3.0.0?

```
3.0.0 = Latest stable, backward compatible, security patches
```

### Why Sentence-Transformers 3.3.1?

```
3.3.1 = Latest stable, includes MiniLM models
```

### Why NumPy 1.26.4?

```
1.26.4 = Latest stable before 2.0 (which has breaking changes)
```

---

## Offline Usage

After first run, the system can work offline:

1. **Models are cached** - Embedding models downloaded and stored locally
2. **Database is local** - ChromaDB doesn't need internet
3. **Only ArXiv searches need internet** - To fetch papers

To work offline:
- Pre-download papers while online
- Embeddings and search work locally
- Can still rate and browse locally-stored papers

---

## Alternative Packages (For Customization)

If you want to experiment:

| Purpose | Current | Alternative |
|---------|---------|-------------|
| Embeddings | sentence-transformers | HuggingFace transformers |
| Vector DB | ChromaDB | Qdrant, FAISS |
| Web Framework | Flask | FastAPI, Django |
| Paper Search | ArXiv | Semantic Scholar, PubMed |

Just update `requirements.txt` and `app.py` code.

---

## Uninstalling

If you want to completely remove everything:

```bash
# Deactivate environment
deactivate

# Delete environment folder
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# Delete data
rm -rf data  # Linux/Mac
rmdir /s data  # Windows
```

---

## Summary

```
✅ 5 core packages
✅ <600MB total space
✅ No system dependencies
✅ No GPU needed
✅ Works on Windows/Mac/Linux
✅ All packages actively maintained
```

Ready to install? Run:

```bash
pip install -r requirements.txt
```

Questions? Check package documentation:
- Flask: https://flask.palletsprojects.com/
- ArXiv: https://github.com/lukasschwab/arxiv.py
- ChromaDB: https://docs.trychroma.com/
- Sentence-Transformers: https://www.sbert.net/
- NumPy: https://numpy.org/
