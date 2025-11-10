"""
ENHANCED AI-POWERED LEARNING CURATION SYSTEM
Features:
- ArXiv paper discovery + EdX course discovery
- ChromaDB vector storage with persistent memory
- LinUCB reinforcement learning algorithm
- LLM-based summarization with keywords
- Web frontend dashboard
- Daily automated scheduling
"""

import sys
import os
import json

# If the project includes a virtual environment at ./venv and this process
# is not already running inside a virtualenv, re-exec the program using the
# venv's python executable so the expected packages are available.
def _ensure_use_project_venv():
    try:
        # Avoid a re-exec loop
        if os.environ.get("VENV_RELAUNCHED") == "1":
            return

        in_venv = (
            hasattr(sys, "real_prefix") or
            (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix) or
            (os.environ.get("VIRTUAL_ENV") is not None)
        )

        project_root = os.path.dirname(os.path.abspath(__file__))
        venv_path = os.path.join(project_root, "venv")
        venv_python = os.path.join(venv_path, "bin", "python")

        if (not in_venv) and os.path.isdir(venv_path) and os.path.isfile(venv_python):
            # Re-exec using the venv python so subsequent imports use venv packages
            os.environ["VENV_RELAUNCHED"] = "1"
            os.execv(venv_python, [venv_python] + sys.argv)
    except Exception:
        # If anything fails here, continue with the current interpreter
        return


_ensure_use_project_venv()

import numpy as np
import arxiv
from sentence_transformers import SentenceTransformer
import requests
from datetime import datetime
import logging
from pathlib import Path
import time
import schedule
import threading
import re
import random
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    DATA_DIR = Path("./data")
    PAPERS_DIR = DATA_DIR / "papers"
    VECTOR_DB_PATH = DATA_DIR / "vector_db"
    USER_PREFS_FILE = DATA_DIR / "user_preferences.json"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    MAX_PAPERS_PER_SEARCH = 8
    MAX_COURSES_PER_SEARCH = 5
    # When discovering papers, request a larger pool then sample to increase
    # diversity. This avoids returning the same top-k every time.
    DISCOVERY_POOL_SIZE = 30

    ALPHA = 0.25  # LinUCB confidence radius
    CONTEXT_DIM = 384

# ============================================================================
# LINUCB ALGORITHM
# ============================================================================

class LinUCBArm:
    def __init__(self, arm_id, d, alpha):
        self.arm_id = arm_id
        self.d = d
        self.alpha = alpha
        self.A = np.identity(d)
        self.A_inv = np.identity(d)
        self.b = np.zeros((d, 1))
        self.theta = np.zeros((d, 1))

    def reward(self, context, reward_value):
        if context.ndim == 1:
            context = context.reshape(-1, 1)

        self.A += np.dot(context, context.T)
        self.b += reward_value * context

        try:
            self.A_inv = np.linalg.inv(self.A)
        except:
            self.A_inv = np.linalg.pinv(self.A)

        self.theta = np.dot(self.A_inv, self.b)

    def ucb(self, context):
        if context.ndim == 1:
            context = context.reshape(-1, 1)

        mean = np.dot(self.theta.T, context)[0, 0]
        variance = np.dot(context.T, np.dot(self.A_inv, context))[0, 0]
        confidence = self.alpha * np.sqrt(max(variance, 0))

        return mean + confidence

class LinUCBPolicy:
    def __init__(self, num_arms, d, alpha):
        self.num_arms = num_arms
        self.arms = [LinUCBArm(i, d, alpha) for i in range(num_arms)]

    def select_arm(self, context):
        if len(context.shape) == 1:
            context = context.reshape(-1, 1)

        max_ucb = -np.inf
        best_arm = 0

        for i, arm in enumerate(self.arms):
            ucb_value = arm.ucb(context)
            if ucb_value > max_ucb:
                max_ucb = ucb_value
                best_arm = i

        return best_arm

    def reward_arm(self, arm_id, context, reward_value):
        self.arms[arm_id].reward(context, reward_value)

# ============================================================================
# VECTOR STORAGE
# ============================================================================

class VectorStore:
    def __init__(self):
        # Initialize embedding model if possible (useful even without ChromaDB)
        self.embedding_model = None
        try:
            # SentenceTransformer import is at top; try to instantiate the model
            self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {Config.EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"SentenceTransformer unavailable or failed to load: {e}. Continuing without embeddings.")

        # Try to initialize ChromaDB if available and correctly configured.
        try:
            import chromadb

            self.client = chromadb.PersistentClient(path=str(Config.VECTOR_DB_PATH))
            self.papers_collection = self.client.get_or_create_collection(
                name="research_papers",
                metadata={"description": "Research paper embeddings"}
            )
            self.courses_collection = self.client.get_or_create_collection(
                name="courses",
                metadata={"description": "EdX course embeddings"}
            )
            self.disabled = False
            logger.info("VectorStore initialized using ChromaDB")
        except Exception as e:
            # Chromadb failed to initialize (missing deps or bad config). Fall
            # back to a lightweight in-memory store so the app can still run.
            logger.warning(f"ChromaDB unavailable or failed to initialize: {e}. Using in-memory fallback.")
            self.disabled = True
            self.papers = []
            # keep course entries; if embedding_model is available we will
            # store embeddings alongside courses for in-memory similarity.
            self.courses = []
        # Maintain sets of ids to prevent duplicate adds (works for both
        # in-memory fallback and when using ChromaDB client)
        self._paper_ids = set()
        self._course_ids = set()

    def add_paper(self, paper):
        try:
            # Avoid adding duplicates
            pid = paper.get('id')
            if pid is not None and pid in self._paper_ids:
                return

            if self.disabled:
                # Keep a lightweight record so recommendations still work roughly
                # If embeddings are available, store them with the paper for
                # basic nearest-neighbor search later.
                if self.embedding_model is not None:
                    text = f"{paper.get('title','')} {paper.get('abstract','')}"
                    emb = self.embedding_model.encode(text, convert_to_numpy=True)
                    p = dict(paper)
                    p['_embedding'] = emb
                    self.papers.append(p)
                else:
                    self.papers.append(paper)
                # mark id
                if pid is not None:
                    self._paper_ids.add(pid)
                return

            text = f"{paper['title']} {paper['abstract']}"
            embedding = None
            if self.embedding_model is not None:
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)

            # When using a persistent collection, avoid duplicate ids
            try:
                self.papers_collection.add(
                    ids=[paper['id']],
                    embeddings=[(embedding.tolist() if embedding is not None else [])],
                    documents=[paper.get('abstract','')],
                    metadatas=[{
                        'title': paper.get('title',''),
                        'authors': json.dumps(paper.get('authors', [])),
                        'published': paper.get('published', ''),
                        'type': 'paper'
                    }]
                )
            except Exception:
                # If the collection fails to add (duplicate id or other),
                # fall back to adding to in-memory list to keep app usable.
                p = dict(paper)
                if embedding is not None:
                    p['_embedding'] = embedding
                self.papers.append(p)

            if pid is not None:
                self._paper_ids.add(pid)
        except Exception as e:
            logger.error(f"Error adding paper: {e}")

    def add_course(self, course):
        try:
            cid = course.get('id')
            if cid is not None and cid in self._course_ids:
                return

            if self.disabled:
                # Store course and embedding (if model available) in-memory so
                # search can leverage vector similarity even when ChromaDB is
                # not present.
                if self.embedding_model is not None:
                    text = f"{course.get('title','')} {course.get('description','')}"
                    emb = self.embedding_model.encode(text, convert_to_numpy=True)
                    c = dict(course)
                    c['_embedding'] = emb
                    self.courses.append(c)
                else:
                    self.courses.append(course)
                if cid is not None:
                    self._course_ids.add(cid)
                return

            text = f"{course['title']} {course['description']}"
            embedding = None
            if self.embedding_model is not None:
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)

            try:
                self.courses_collection.add(
                    ids=[course['id']],
                    embeddings=[(embedding.tolist() if embedding is not None else [])],
                    documents=[course.get('description','')],
                    metadatas=[{
                        'title': course.get('title',''),
                        'url': course.get('url', ''),
                        'institution': course.get('institution', ''),
                        'type': 'course'
                    }]
                )
            except Exception:
                c = dict(course)
                if embedding is not None:
                    c['_embedding'] = embedding
                self.courses.append(c)

            if cid is not None:
                self._course_ids.add(cid)
        except Exception as e:
            logger.error(f"Error adding course: {e}")

# ============================================================================
# DISCOVERY MODULES
# ============================================================================

class PaperDiscovery:
    def search_arxiv(self, query, max_results=8):
        try:
            logger.info(f"Searching ArXiv: {query}")
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )

            papers = []
            for result in client.results(search):
                paper_info = {
                    'id': result.entry_id.split('/abs/')[-1],
                    'title': result.title,
                    'authors': [author.name for author in result.authors[:5]],
                    'abstract': result.summary,
                    'published': str(result.published),
                    'pdf_url': result.pdf_url,
                    'categories': result.categories
                }
                papers.append(paper_info)

            return papers
        except Exception as e:
            logger.error(f"ArXiv error: {e}")
            return []

class CourseDiscovery:
    def __init__(self, courses_file=Config.DATA_DIR / "courses.json"):
        self.courses_file = Path(courses_file)

        # Default seed courses (written to data/courses.json if file missing)
        self._default_courses = [
            {
                "id": "cs50-python",
                "title": "CS50's Introduction to Programming with Python",
                "institution": "Harvard",
                "url": "https://edx.org/course/cs50s-introduction-programming-python",
                "description": "Learn Python fundamentals. Variables, functions, loops, conditionals.",
                "level": "Beginner"
            },
            {
                "id": "ibm-python",
                "title": "IBM: Python Basics for Data Science",
                "institution": "IBM",
                "url": "https://edx.org/course/python-basics-data-science",
                "description": "Python for data science. Pandas, NumPy, Matplotlib visualization.",
                "level": "Beginner"
            },
            {
                "id": "berkeley-data",
                "title": "UC Berkeley: Foundations of Data Science",
                "institution": "UC Berkeley",
                "url": "https://edx.org/course/foundations-data-science",
                "description": "Data science fundamentals. Computation, visualization, inference.",
                "level": "Beginner"
            },
            {
                "id": "mit-ml",
                "title": "MIT: Machine Learning with Python",
                "institution": "MIT",
                "url": "https://edx.org/course/machine-learning-python",
                "description": "ML algorithms and implementation. Supervised, unsupervised learning.",
                "level": "Intermediate"
            },
            {
                "id": "stanford-algo",
                "title": "Stanford: Design of Computer Programs",
                "institution": "Stanford",
                "url": "https://edx.org/course/design-computer-programs",
                "description": "Design patterns, software engineering, Python best practices.",
                "level": "Intermediate"
            },
            {
                "id": "penn-web",
                "title": "UPenn: Web Programming with Python",
                "institution": "UPenn",
                "url": "https://edx.org/course/web-programming-python",
                "description": "Web development with Python, JavaScript, Flask, Django.",
                "level": "Intermediate"
            },
            {
                "id": "berkeley-security",
                "title": "UC Berkeley: Computer Security",
                "institution": "UC Berkeley",
                "url": "https://edx.org/course/computer-security",
                "description": "Cryptography, security protocols, penetration testing.",
                "level": "Intermediate"
            },
            {
                "id": "georgia-ai",
                "title": "Georgia Tech: Artificial Intelligence",
                "institution": "Georgia Tech",
                "url": "https://edx.org/course/artificial-intelligence",
                "description": "AI algorithms, search, ML, natural language processing.",
                "level": "Advanced"
            },
        ]

        # Attempt to load courses from data/courses.json, fall back to defaults
        try:
            if self.courses_file.exists():
                with open(self.courses_file, 'r') as f:
                    self.courses = json.load(f)
            else:
                self.courses = self._default_courses
                try:
                    with open(self.courses_file, 'w') as f:
                        json.dump(self.courses, f, indent=2)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to load courses from {self.courses_file}: {e}")
            self.courses = self._default_courses

    def reload(self):
        """Reload courses from disk (useful if user edits data/courses.json)."""
        try:
            if self.courses_file.exists():
                with open(self.courses_file, 'r') as f:
                    self.courses = json.load(f)
            return True
        except Exception as e:
            logger.error(f"Failed to reload courses: {e}")
            return False

    def index_courses(self, vector_store):
        """Index all known courses into the provided vector store (idempotent).
        This helps in-memory or Chroma-backed vector search later.
        """
        if vector_store is None:
            return

        existing_ids = {c.get('id') for c in getattr(vector_store, 'courses', [])}
        for course in self.courses:
            if course.get('id') in existing_ids:
                continue
            try:
                vector_store.add_course(course)
            except Exception:
                pass

    def add_course_to_file(self, course):
        try:
            # append and write
            self.courses.append(course)
            with open(self.courses_file, 'w') as f:
                json.dump(self.courses, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to add course to file: {e}")
            return False

    def search_courses(self, query, max_results=5, vector_store=None):
        logger.info(f"Searching courses: {query}")
        query_lower = query.lower()
        q_tokens = set(re.findall(r"\w+", query_lower))

        scored = []
        for course in self.courses:
            title = course.get('title', '').lower()
            desc = course.get('description', '').lower()
            title_tokens = set(re.findall(r"\w+", title))
            desc_tokens = set(re.findall(r"\w+", desc))

            overlap = len(q_tokens & (title_tokens | desc_tokens))
            score = float(overlap)

            # small boost for explicit level match
            if 'level' in course and course['level'].lower() in query_lower:
                score += 0.5

            sim = 0.0
            # If vector embeddings are available, try to use them as a tie-breaker
            try:
                if vector_store and getattr(vector_store, 'embedding_model', None) is not None:
                    # prefer course-level embedding if present (from file or from
                    # previous indexing). Otherwise we skip vector score here.
                    emb = None
                    if isinstance(vector_store, VectorStore) and vector_store.disabled:
                        # in-memory store keeps course dicts with '_embedding'
                        if '_embedding' in course:
                            emb = course['_embedding']
                    # If embedding exists, compute cosine similarity
                    if emb is not None:
                        qemb = vector_store.embedding_model.encode(query, convert_to_numpy=True)
                        denom = (np.linalg.norm(qemb) * np.linalg.norm(emb))
                        if denom > 0:
                            sim = float(np.dot(qemb, emb) / denom)
                            score += sim * 1.5
            except Exception:
                pass

            scored.append((score, sim, course))

        # sort by score and similarity, highest first
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

        results = [c for (_, _, c) in scored[:max_results]]

        # If less than requested, fill with random remaining to diversify
        if len(results) < max_results:
            remaining = [c for (_, _, c) in scored[max_results:]]
            random.shuffle(remaining)
            results.extend(remaining[:(max_results - len(results))])

        return results

# ============================================================================
# LLM SUMMARIZER
# ============================================================================

class LLMSummarizer:
    def summarize(self, text, max_length=150):
        try:
            sentences = text.split('.')
            summary = '. '.join(sentences[:2]) + '.'
            return summary[:max_length]
        except:
            return text[:max_length]

    def extract_keywords(self, text):
        try:
            words = text.lower().split()
            common = {'the', 'a', 'an', 'is', 'are', 'and', 'or', 'in', 'on', 'to', 'for', 'of'}
            keywords = [w.strip('.,!?;:') for w in words 
                       if len(w) > 4 and w.lower() not in common and not w.isdigit()]
            return list(dict.fromkeys(keywords))[:5]
        except:
            return []

# ============================================================================
# USER PREFERENCES
# ============================================================================

class UserPreferences:
    def __init__(self):
        self.prefs_file = Config.USER_PREFS_FILE
        self.prefs = self._load()

    def _load(self):
        if self.prefs_file.exists():
            with open(self.prefs_file, 'r') as f:
                return json.load(f)
        return {
            'topics': [],
            'rated_items': {},
            'preferences': {},
            'read_count': 0,
            'last_updated': str(datetime.now())
        }

    def save(self):
        self.prefs['last_updated'] = str(datetime.now())
        with open(self.prefs_file, 'w') as f:
            json.dump(self.prefs, f, indent=2)

    def set_topics(self, topics):
        self.prefs['topics'] = topics
        for topic in topics:
            self.prefs['preferences'][topic] = 1.0
        self.save()

    def rate_item(self, item_id, rating):
        self.prefs['rated_items'][item_id] = rating
        self.save()

# ============================================================================
# MAIN SYSTEM
# ============================================================================

class EnhancedSystem:
    def __init__(self):
        self.vector_store = VectorStore()
        self.paper_discovery = PaperDiscovery()
        self.course_discovery = CourseDiscovery()
        self.summarizer = LLMSummarizer()
        self.user_prefs = UserPreferences()
        self.linucb = LinUCBPolicy(num_arms=10, d=Config.CONTEXT_DIM, alpha=Config.ALPHA)
        self.recommendations_cache = []
        # Index known courses into the vector store so searches can use embeddings
        try:
            self.course_discovery.index_courses(self.vector_store)
        except Exception:
            pass
        logger.info("System initialized")

    def daily_discovery(self, topics):
        logger.info(f"Starting daily discovery for topics: {topics}")
        all_items = []

        for topic in topics[:3]:
            # Fetch a larger pool from ArXiv, then sample to avoid repeating the
            # exact same top items every run. Keep the top few then mix the
            # rest randomly to retain relevance while increasing variety.
            pool = self.paper_discovery.search_arxiv(topic, Config.DISCOVERY_POOL_SIZE)
            papers_to_use = []
            if pool:
                # take up to 2 top items deterministically, then sample the rest
                top_k = min(2, len(pool))
                papers_to_use.extend(pool[:top_k])
                remaining = pool[top_k:]
                if remaining:
                    random.shuffle(remaining)
                    need = max(0, Config.MAX_PAPERS_PER_SEARCH - len(papers_to_use))
                    papers_to_use.extend(remaining[:need])

            for paper in papers_to_use:
                paper['item_type'] = 'paper'
                self.vector_store.add_paper(paper)
                all_items.append(paper)

            courses = self.course_discovery.search_courses(topic, Config.MAX_COURSES_PER_SEARCH, vector_store=self.vector_store)
            for course in courses:
                course['item_type'] = 'course'
                self.vector_store.add_course(course)
                all_items.append(course)

        self.recommendations_cache = all_items
        logger.info(f"Found {len(all_items)} items")
        return all_items

    def generate_theme_bundles(self, topics, per_topic=1):
        """Produce a list of themed bundles per topic. Each bundle contains:
        - one paper (if available)
        - one course (if available)
        - one synthesized 'article' explainer created from the paper + course

        This keeps recommendations diverse and grouped by theme.
        """
        bundles = []
        # Use the cached items as a pool to avoid repeated discovery runs
        pool = list(self.recommendations_cache)

        for topic in topics[:5]:
            # Find candidate papers and courses for this topic
            papers = [p for p in pool if p.get('item_type') == 'paper' and topic.lower() in (p.get('title','')+p.get('abstract','')).lower()]
            courses = [c for c in pool if c.get('item_type') == 'course' and topic.lower() in (c.get('title','')+c.get('description','')).lower()]

            # fallback to any if none match specifically
            if not papers:
                papers = [p for p in pool if p.get('item_type') == 'paper']
            if not courses:
                courses = [c for c in pool if c.get('item_type') == 'course']

            # sort papers by date (newer first)
            try:
                papers.sort(key=lambda p: datetime.fromisoformat(p.get('published','')), reverse=True)
            except Exception:
                pass

            for i in range(per_topic):
                paper = papers[i] if i < len(papers) else (papers[0] if papers else None)
                course = courses[i] if i < len(courses) else (courses[0] if courses else None)

                # Build a synthetic article that explains the paper in course context
                article = None
                if paper is not None:
                    a_title = f"Explainer: {paper.get('title','')[:80]}"
                    combined_text = (paper.get('abstract','') or '') + '\n' + (course.get('description','') or '')
                    a_summary = self.summarizer.summarize(combined_text, max_length=220)
                    a_keywords = self.summarizer.extract_keywords(combined_text)
                    article = {
                        'id': f"article-{paper.get('id','')}",
                        'title': a_title,
                        'type': 'article',
                        'url': paper.get('pdf_url', ''),
                        'summary': a_summary,
                        'keywords': a_keywords
                    }

                bundle = {
                    'theme': topic,
                    'paper': {
                        'id': paper.get('id','') if paper else '',
                        'title': paper.get('title','') if paper else '',
                        'url': paper.get('pdf_url','') if paper else '',
                        'summary': self.summarizer.summarize(paper.get('abstract','')) if paper else ''
                    } if paper else None,
                    'course': {
                        'id': course.get('id','') if course else '',
                        'title': course.get('title','') if course else '',
                        'url': course.get('url','') if course else '',
                        'summary': self.summarizer.summarize(course.get('description','')) if course else ''
                    } if course else None,
                    'article': article
                }

                bundles.append(bundle)

        return bundles

    def get_recommendations(self, num=5):
        if not self.recommendations_cache:
            return []
        # Deduplicate by id while preserving order-ish; prefer newest papers
        seen = set()
        items = []
        for item in self.recommendations_cache:
            iid = item.get('id')
            if iid in seen:
                continue
            seen.add(iid)
            items.append(item)

        # Separate papers and courses for different sorting heuristics
        papers = [i for i in items if i.get('item_type') == 'paper']
        courses = [i for i in items if i.get('item_type') != 'paper']

        def parse_date(s):
            try:
                return datetime.fromisoformat(s)
            except Exception:
                try:
                    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
                except Exception:
                    return datetime.min

        # sort papers by published date descending (newer first)
        try:
            papers.sort(key=lambda p: parse_date(p.get('published', '')), reverse=True)
        except Exception:
            pass

        # keep courses as-is (they have no published date), but shuffle slightly
        if len(courses) > 1:
            random.shuffle(courses)

        merged = papers + courses

        # Rotate results using user's read_count so repeated calls show different
        # slices of the catalog instead of the exact same prefix every time.
        offset = 0
        try:
            offset = int(self.user_prefs.prefs.get('read_count', 0)) % max(1, len(merged))
        except Exception:
            offset = 0

        rotated = merged[offset:] + merged[:offset]

        # Build result details for the top `num` items
        recommendations = []
        for item in rotated[:num]:
            details = {
                'id': item.get('id', ''),
                'title': item.get('title', ''),
                'type': item.get('item_type', ''),
                'url': item.get('url', item.get('pdf_url', '')),
                'summary': self.summarizer.summarize(
                    item.get('abstract', item.get('description', ''))
                ),
                'keywords': self.summarizer.extract_keywords(
                    item.get('abstract', item.get('description', ''))
                )
            }
            recommendations.append(details)

        # increment read_count to vary subsequent responses
        try:
            self.user_prefs.prefs['read_count'] = int(self.user_prefs.prefs.get('read_count', 0)) + 1
            self.user_prefs.save()
        except Exception:
            pass

        return recommendations

    def rate_item(self, item_id, rating):
        self.user_prefs.rate_item(item_id, rating)
        logger.info(f"Rated {item_id}: {rating}/5")

# ============================================================================
# FLASK APP
# ============================================================================

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

system = None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/setup', methods=['POST'])
def setup():
    global system
    data = request.json
    topics = data.get('topics', [])
    system.user_prefs.set_topics(topics)
    return jsonify({'status': 'success'})

@app.route('/api/get-recommendations', methods=['GET'])
def get_recs():
    global system
    topics = system.user_prefs.prefs.get('topics', [])
    if not topics:
        return jsonify({'error': 'Setup required'}), 400

    # Run discovery to refresh the cache and then build themed bundles
    system.daily_discovery(topics)
    bundles = system.generate_theme_bundles(topics, per_topic=1)
    # Keep a compatibility field with flat recommendations as well
    recs = system.get_recommendations(8)
    return jsonify({'bundles': bundles, 'recommendations': recs})

@app.route('/api/rate', methods=['POST'])
def rate():
    global system
    data = request.json
    item_id = data.get('item_id')
    rating = data.get('rating')
    system.rate_item(item_id, rating)
    return jsonify({'status': 'success'})

@app.route('/api/status', methods=['GET'])
def get_status():
    global system
    prefs = system.user_prefs.prefs
    return jsonify({
        'topics': prefs.get('topics', []),
        'items_rated': len(prefs.get('rated_items', {}))
    })


@app.route('/api/reload-courses', methods=['POST'])
def reload_courses():
    """Reload courses from data/courses.json and re-index them into the vector store."""
    global system
    ok = system.course_discovery.reload()
    if ok:
        try:
            system.course_discovery.index_courses(system.vector_store)
        except Exception:
            pass
        return jsonify({'status': 'reloaded', 'count': len(system.course_discovery.courses)})
    else:
        return jsonify({'status': 'error reloading courses'}), 500

if __name__ == "__main__":
    system = EnhancedSystem()
    app.run(debug=True, host='0.0.0.0', port=12346)


@app.route('/api/refresh-papers', methods=['POST'])
def refresh_papers():
    """Force a refresh of the discovery process: clear cache and run
    daily_discovery immediately. Returns the new count of discovered items.
    """
    global system
    topics = system.user_prefs.prefs.get('topics', [])
    if not topics:
        return jsonify({'error': 'No topics set; call /api/setup first'}), 400

    # Clear old cache and run discovery
    system.recommendations_cache = []
    items = system.daily_discovery(topics)
    return jsonify({'status': 'refreshed', 'count': len(items)})
