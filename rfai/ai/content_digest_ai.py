"""
Content Digest AI - Automatically summarizes and creates notes from consumed content

This system watches what you read/watch and auto-generates:
- Concise summaries
- Key concepts list
- Flashcards for Spaced Repetition
- Connection to other topics you've learned
"""

from anthropic import Anthropic
from typing import List, Dict
import fitz  # PyMuPDF for PDF extraction
from youtube_transcript_api import YouTubeTranscriptApi
import re

class ContentDigestAI:
    """
    Processes consumed content and generates learning materials.
    
    Supported content types:
    - PDFs (papers, books)
    - YouTube videos (via transcripts)
    - Articles (web scraping)
    - Code repositories (via README + code analysis)
    """
    
    def __init__(self, anthropic_api_key: str, db_connection):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.db = db_connection
        
    def process_content(
        self,
        content_id: str,
        content_type: str,
        source_url: str = None,
        local_path: str = None
    ) -> Dict:
        """
        Main entry point: extract content and generate digest.
        """
        
        # Step 1: Extract raw content
        raw_text = self._extract_content(content_type, source_url, local_path)
        
        if not raw_text or len(raw_text) < 100:
            return {"error": "Content too short or extraction failed"}
        
        # Step 2: Generate comprehensive digest using Claude
        digest = self._generate_digest(raw_text, content_type)
        
        # Step 3: Store in database
        self._store_digest(content_id, digest)
        
        # Step 4: Generate flashcards
        flashcards = self._generate_flashcards(digest)
        
        # Step 5: Find connections to other learned content
        connections = self._find_connections(digest)
        
        return {
            "content_id": content_id,
            "digest": digest,
            "flashcards": flashcards,
            "connections": connections,
            "word_count": len(raw_text.split()),
            "estimated_read_time_min": len(raw_text.split()) / 200
        }
    
    def _extract_content(
        self,
        content_type: str,
        source_url: str = None,
        local_path: str = None
    ) -> str:
        """
        Extract text from various content types.
        """
        
        if content_type == "pdf":
            return self._extract_pdf(local_path)
        
        elif content_type == "youtube":
            video_id = self._extract_video_id(source_url)
            return self._extract_youtube_transcript(video_id)
        
        elif content_type == "article":
            return self._extract_article(source_url)
        
        elif content_type == "github_repo":
            return self._extract_github_readme(source_url)
        
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    def _extract_pdf(self, path: str) -> str:
        """Extract text from PDF using PyMuPDF."""
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    def _extract_youtube_transcript(self, video_id: str) -> str:
        """Get YouTube transcript."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = " ".join([entry['text'] for entry in transcript_list])
            return transcript
        except Exception as e:
            return f"Error fetching transcript: {e}"
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        match = re.search(r'(?:v=|/)([\w-]{11})', url)
        return match.group(1) if match else None
    
    def _extract_article(self, url: str) -> str:
        """
        Extract article text using newspaper3k or trafilatura.
        """
        from trafilatura import fetch_url, extract
        
        downloaded = fetch_url(url)
        text = extract(downloaded)
        return text if text else ""
    
    def _extract_github_readme(self, repo_url: str) -> str:
        """
        Fetch README from GitHub repo.
        """
        import requests
        
        # Convert repo URL to raw README URL
        parts = repo_url.split('github.com/')[1].split('/')
        owner, repo = parts[0], parts[1]
        
        readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        
        response = requests.get(readme_url)
        if response.status_code == 200:
            return response.text
        
        # Try master branch
        readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
        response = requests.get(readme_url)
        return response.text if response.status_code == 200 else ""
    
    def _generate_digest(self, raw_text: str, content_type: str) -> Dict:
        """
        Use Claude to generate comprehensive digest.
        """
        
        # Truncate if too long (Claude context limit)
        max_chars = 80000  # ~20k tokens
        if len(raw_text) > max_chars:
            raw_text = raw_text[:max_chars] + "\n\n[TRUNCATED]"
        
        prompt = f"""
You are an expert learning assistant. I just consumed this content:

CONTENT TYPE: {content_type}

CONTENT:
{raw_text}

Generate a comprehensive learning digest with:

1. **TL;DR** (2-3 sentences, high-level summary)

2. **Key Concepts** (bullet list of main ideas)

3. **Detailed Summary** (3-5 paragraphs explaining the content)

4. **Important Definitions** (technical terms defined)

5. **Prerequisites** (what you should know before this)

6. **Follow-Up Topics** (what to learn next)

7. **Practical Applications** (how to use this knowledge)

8. **Quiz Questions** (5 questions to test understanding)

Output as JSON:
{{
  "tldr": "...",
  "key_concepts": ["...", "..."],
  "detailed_summary": "...",
  "definitions": {{"term": "definition", ...}},
  "prerequisites": ["..."],
  "follow_up_topics": ["..."],
  "applications": ["..."],
  "quiz": [
    {{"q": "...", "a": "...", "difficulty": "easy|medium|hard"}}
  ]
}}
"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse JSON response
        import json
        digest_json = response.content[0].text
        
        # Extract JSON (might be wrapped in markdown)
        if "```json" in digest_json:
            digest_json = digest_json.split("```json")[1].split("```")[0]
        
        return json.loads(digest_json)
    
    def _generate_flashcards(self, digest: Dict) -> List[Dict]:
        """
        Convert digest into flashcards for Spaced Repetition.
        """
        
        flashcards = []
        
        # From definitions
        for term, definition in digest.get("definitions", {}).items():
            flashcards.append({
                "front": f"What is {term}?",
                "back": definition,
                "type": "definition",
                "difficulty": "easy"
            })
        
        # From quiz questions
        for quiz_item in digest.get("quiz", []):
            flashcards.append({
                "front": quiz_item['q'],
                "back": quiz_item['a'],
                "type": "quiz",
                "difficulty": quiz_item.get('difficulty', 'medium')
            })
        
        # From key concepts (concept -> explanation)
        for concept in digest.get("key_concepts", []):
            flashcards.append({
                "front": f"Explain: {concept}",
                "back": f"(See detailed summary for explanation of {concept})",
                "type": "concept",
                "difficulty": "medium"
            })
        
        return flashcards
    
    def _find_connections(self, digest: Dict) -> List[Dict]:
        """
        Find connections to previously learned content using embeddings.
        """
        
        # Embed the new content's key concepts
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        new_content_text = " ".join(digest.get("key_concepts", []))
        new_embedding = model.encode(new_content_text)
        
        # Query vector DB for similar content
        # (Assume ChromaDB is set up)
        from chromadb import Client
        
        chroma_client = Client()
        collection = chroma_client.get_or_create_collection("content_embeddings")
        
        results = collection.query(
            query_embeddings=[new_embedding.tolist()],
            n_results=5
        )
        
        connections = []
        for i, doc_id in enumerate(results['ids'][0]):
            similarity = 1 - results['distances'][0][i]  # Convert distance to similarity
            
            if similarity > 0.7:  # High similarity threshold
                connections.append({
                    "related_content_id": doc_id,
                    "similarity_score": similarity,
                    "reason": "Similar concepts/keywords"
                })
        
        return connections
    
    def _store_digest(self, content_id: str, digest: Dict):
        """
        Store digest in database for future reference.
        """
        
        import json
        
        query = """
        INSERT INTO content_digests (content_id, tldr, key_concepts, detailed_summary, 
                                     definitions, prerequisites, follow_up_topics, 
                                     applications, quiz, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """
        
        self.db.execute(query, (
            content_id,
            digest.get('tldr'),
            json.dumps(digest.get('key_concepts', [])),
            digest.get('detailed_summary'),
            json.dumps(digest.get('definitions', {})),
            json.dumps(digest.get('prerequisites', [])),
            json.dumps(digest.get('follow_up_topics', [])),
            json.dumps(digest.get('applications', [])),
            json.dumps(digest.get('quiz', []))
        ))
        
        self.db.commit()


# Library Requirements:
# - anthropic (Claude API)
# - PyMuPDF / fitz (PDF extraction)
# - youtube-transcript-api (YouTube transcripts)
# - trafilatura (web article extraction)
# - sentence-transformers (embeddings)
# - chromadb (vector database)
# - requests (HTTP requests)

# Database Schema Addition:
"""
CREATE TABLE content_digests (
  id TEXT PRIMARY KEY,
  content_id TEXT,
  tldr TEXT,
  key_concepts TEXT,  -- JSON array
  detailed_summary TEXT,
  definitions TEXT,  -- JSON object
  prerequisites TEXT,  -- JSON array
  follow_up_topics TEXT,  -- JSON array
  applications TEXT,  -- JSON array
  quiz TEXT,  -- JSON array
  created_at DATETIME,
  FOREIGN KEY (content_id) REFERENCES ratings(content_id)
);
"""
