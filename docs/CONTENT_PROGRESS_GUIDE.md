# Content Fetching & Progress Tracking - Complete Guide

## Overview

Your system now **fetches actual content** and **tracks learning progress** through quizzes!

### What's New

1. **Real Content Fetching** - Gets actual YouTube videos, research papers, and movies
2. **Study Plan Integration** - Uses Perplexity AI to recommend content from your study plan
3. **Progress Testing** - Generate quizzes to monitor learning in each subject
4. **Dashboard Integration** - Content displayed automatically based on time block

---

## 1. Content Fetching System

### YouTube Videos

**Fetch Science Videos:**
```bash
curl "http://localhost:5001/api/fetch/youtube/science?max_results=10"
```

**Response:**
```json
{
  "videos": [
    {
      "id": "dQw4w9WgXcQ",
      "title": "Quantum Mechanics Explained",
      "channel": "PBS Space Time",
      "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "duration": "15:30",
      "views": 1250000,
      "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
      "description": "Learn quantum mechanics basics...",
      "published": "2024-12-01"
    }
  ],
  "count": 10,
  "source": "youtube_api" or "sample_data"
}
```

**Fetch Self-Help Videos:**
```bash
curl "http://localhost:5001/api/fetch/youtube/selfhelp?max_results=10"
```

### Research Papers

**Fetch Papers from ArXiv:**
```bash
curl "http://localhost:5001/api/fetch/papers?max_results=10"
```

**Response:**
```json
{
  "papers": [
    {
      "id": "arxiv.2024.12345",
      "title": "Quantum Computing Algorithms",
      "authors": ["John Doe", "Jane Smith"],
      "abstract": "This paper presents...",
      "url": "https://arxiv.org/abs/2024.12345",
      "published": "2024-12-01",
      "categories": ["quant-ph", "cs.AI"]
    }
  ],
  "count": 10,
  "source": "arxiv_api"
}
```

### Movies

**Fetch Movie Recommendations:**
```bash
curl "http://localhost:5001/api/fetch/movies?max_results=10"
```

**Response:**
```json
{
  "movies": [
    {
      "id": "tt0111161",
      "title": "The Shawshank Redemption",
      "director": "Frank Darabont",
      "year": 1994,
      "rating": 9.3,
      "genres": ["Drama"],
      "runtime": "142 min",
      "url": "https://www.imdb.com/title/tt0111161/",
      "poster": "https://m.media-amazon.com/images/..."
    }
  ],
  "count": 10,
  "source": "imdb_api"
}
```

### Current Block Content

**Get Content for Active Time Block:**
```bash
curl "http://localhost:5001/api/fetch/current-block-content"
```

**Response (Science Block Example):**
```json
{
  "active": true,
  "block": {
    "name": "Science Block",
    "content_type": "science_youtube_and_papers",
    "start_time": "09:00",
    "end_time": "12:00"
  },
  "content": {
    "youtube_videos": [...],
    "research_papers": [...]
  }
}
```

---

## 2. Study Plan Integration (Perplexity AI)

### Get Recommendations from Study Plan

**Endpoint:** `POST /api/fetch/study-plan-content`

```bash
curl -X POST "http://localhost:5001/api/fetch/study-plan-content" \
  -H "Content-Type: application/json" \
  -d '{
    "study_plan": "I want to learn:\n1. Quantum Computing\n2. Machine Learning\n3. Deep Learning"
  }'
```

**Response:**
```json
{
  "recommendations": "Based on your study plan, here are recommendations:\n\n1. YouTube Channels:\n   - 3Blue1Brown for math visualizations\n   - Stanford Online for ML courses\n   ...\n\n2. Research Papers:\n   - 'Attention Is All You Need' (Transformers)\n   - 'Playing Atari with Deep RL'\n   ...\n\n3. Books:\n   - 'Quantum Computation and Quantum Information'\n   - 'Deep Learning' by Goodfellow\n   ...",
  "sources": [
    "https://arxiv.org/...",
    "https://www.youtube.com/..."
  ],
  "generated_at": "perplexity",
  "study_plan": "I want to learn..."
}
```

**What It Does:**
- Sends your study plan to Perplexity AI
- Gets personalized content recommendations
- Returns YouTube channels, papers, books, key topics
- Includes citations/sources

**API Key Required:**
Set `PERPLEXITY_API_KEY` environment variable. Get key from: https://www.perplexity.ai/

**Fallback Mode:**
If no API key, returns general guidance based on study plan text.

---

## 3. Progress Testing & Quizzes

### Generate a Quiz

**Endpoint:** `POST /api/quiz/generate`

```bash
curl -X POST "http://localhost:5001/api/quiz/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Quantum Computing",
    "difficulty": "medium",
    "num_questions": 10
  }'
```

**Response:**
```json
{
  "quiz_id": "abc123-def456-...",
  "topic": "Quantum Computing",
  "difficulty": "medium",
  "num_questions": 10,
  "created_at": "2024-12-17T10:30:00",
  "time_limit_minutes": 20,
  "questions": [
    {
      "question_id": "q1",
      "question_text": "What is superposition in quantum computing?",
      "type": "multiple_choice",
      "options": [
        {"id": "a", "text": "Qubits in multiple states simultaneously"},
        {"id": "b", "text": "Classical bit states"},
        {"id": "c", "text": "Error correction method"},
        {"id": "d", "text": "Quantum gate operation"}
      ],
      "correct_answer": "a",
      "explanation": "Superposition allows qubits to exist in multiple states...",
      "points": 10
    }
  ]
}
```

### Submit Quiz Answers

**Endpoint:** `POST /api/quiz/<quiz_id>/submit`

```bash
curl -X POST "http://localhost:5001/api/quiz/abc123/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "q1": "a",
      "q2": "c",
      "q3": "b",
      "q4": "a",
      "q5": "d"
    }
  }'
```

**Response:**
```json
{
  "quiz_id": "abc123",
  "topic": "Quantum Computing",
  "total_questions": 5,
  "correct_count": 4,
  "incorrect_count": 1,
  "score_percentage": 80.0,
  "points_earned": 40,
  "points_possible": 50,
  "results_by_question": [
    {
      "question_id": "q1",
      "question_text": "What is superposition?",
      "user_answer": "a",
      "correct_answer": "a",
      "is_correct": true,
      "explanation": "Superposition allows...",
      "points_earned": 10,
      "points_possible": 10
    },
    {
      "question_id": "q2",
      "question_text": "What is entanglement?",
      "user_answer": "c",
      "correct_answer": "b",
      "is_correct": false,
      "explanation": "Entanglement is...",
      "points_earned": 0,
      "points_possible": 10
    }
  ],
  "submitted_at": "2024-12-17T10:35:00"
}
```

### View Progress Summary

**Endpoint:** `GET /api/progress/summary`

```bash
# All topics
curl "http://localhost:5001/api/progress/summary"

# Specific topic
curl "http://localhost:5001/api/progress/summary?topic=Quantum Computing"
```

**Response:**
```json
{
  "total_quizzes": 15,
  "average_score": 82.5,
  "topics_covered": [
    "Quantum Computing",
    "Machine Learning",
    "Deep Learning"
  ],
  "recent_quizzes": [
    {
      "quiz_id": "abc123",
      "topic": "Quantum Computing",
      "submitted_at": "2024-12-17T10:35:00",
      "score_percentage": 80.0,
      "correct_count": 4,
      "total_questions": 5
    }
  ],
  "highest_score": 95.0,
  "lowest_score": 65.0
}
```

---

## 4. Dashboard Integration

### How Content Appears

The dashboard automatically:

1. **Detects Current Time Block**
   - Science Block (09:00-12:00)
   - Self-Help Block (13:00-14:00)
   - Movie Block (18:00-19:30)

2. **Fetches Relevant Content**
   - Calls `/api/fetch/current-block-content`
   - Gets videos/papers/movies for that block
   - Displays in grid layout

3. **Shows Visual Cards**
   - YouTube videos with thumbnails, titles, channels
   - Research papers with abstracts, authors
   - Movies with posters, ratings, directors

4. **Clickable Links**
   - Each item links to source (YouTube, ArXiv, IMDB)
   - Opens in new tab

### Example Dashboard Content

**During Science Block:**
```
📺 Recommended Videos
┌─────────────────────────────────┐
│ [Thumbnail]                     │
│ Quantum Mechanics Explained     │
│ PBS Space Time                  │
│ 15:30 • 1.2M views             │
└─────────────────────────────────┘

📄 Research Papers
┌─────────────────────────────────┐
│ Quantum Computing Algorithms    │
│ John Doe, Jane Smith            │
│ This paper presents...          │
│ 2024-12-01 • quant-ph, cs.AI   │
└─────────────────────────────────┘
```

**During Movie Block:**
```
🎬 Film Recommendations
┌─────────────────────────────────┐
│ [Movie Poster]                  │
│ The Shawshank Redemption       │
│ Frank Darabont                  │
│ 1994 • ⭐ 9.3                   │
│ 142 min                         │
└─────────────────────────────────┘
```

---

## 5. API Configuration

### Required API Keys

Add to `.env` file or environment:

```bash
# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key

# Perplexity AI
PERPLEXITY_API_KEY=your_perplexity_api_key

# IMDB (optional - using OMDb API)
OMDB_API_KEY=your_omdb_api_key
```

### How to Get Keys

**YouTube API:**
1. Go to https://console.cloud.google.com/
2. Create project
3. Enable YouTube Data API v3
4. Create credentials → API key
5. Copy key

**Perplexity API:**
1. Go to https://www.perplexity.ai/
2. Sign up for API access
3. Copy API key from dashboard

**IMDB/OMDb:**
1. Go to http://www.omdbapi.com/apikey.aspx
2. Request free key
3. Verify email
4. Copy key

### Fallback Mode

**Without API keys**, the system uses:
- Sample data for YouTube/movies
- ArXiv public API (no key needed)
- Template-based study plan recommendations

---

## 6. Testing the System

### Run Comprehensive Test

```bash
python test_content_and_progress.py
```

**What It Tests:**
1. ✅ Fetch science YouTube videos
2. ✅ Fetch self-help YouTube videos
3. ✅ Fetch research papers from ArXiv
4. ✅ Fetch movie recommendations
5. ✅ Get current block content
6. ✅ Generate study plan recommendations
7. ✅ Generate quiz
8. ✅ Submit quiz answers
9. ✅ View progress summary

**Output:**
```
══════════════════════════════════════════════════════════════════
  1. Fetching Science YouTube Videos
══════════════════════════════════════════════════════════════════
Source: sample_data
Videos found: 5

1. Quantum Mechanics - Educational Overview
   Channel: Sample Channel
   URL: https://youtube.com/watch?v=sample0
   Duration: 15:30

...

✅ All features working!
```

---

## 7. Workflow Examples

### Example 1: Morning Study Session

**9:00 AM - Science Block Starts**

1. User opens dashboard
2. System shows Science Block active
3. Dashboard fetches:
   - 5 quantum mechanics videos
   - 5 recent ArXiv papers on quantum computing
4. User clicks video, watches for 20 minutes
5. Page tracker logs: "Chrome - Quantum Mechanics Video"
6. After video, user takes quiz:
   ```bash
   POST /api/quiz/generate
   {
     "topic": "Quantum Mechanics",
     "difficulty": "easy",
     "num_questions": 5
   }
   ```
7. User answers quiz
8. System shows: 80% score, weak areas identified

### Example 2: Study Plan Setup

**New User Workflow:**

1. User writes study plan:
   ```
   I want to learn:
   - Quantum computing fundamentals
   - Quantum algorithms (Shor's, Grover's)
   - Quantum error correction
   - Quantum machine learning
   ```

2. System sends to Perplexity:
   ```bash
   POST /api/fetch/study-plan-content
   {"study_plan": "..."}
   ```

3. Perplexity returns:
   - Top YouTube channels: 3Blue1Brown, Qiskit
   - Key papers: Nielsen & Chuang textbook, latest ArXiv papers
   - Online courses: IBM Quantum, MIT OpenCourseWare
   - Practice: Qiskit tutorials, coding exercises

4. User updates `interests.json` with topics

5. System now fetches relevant content automatically

### Example 3: Progress Tracking

**Monthly Review:**

1. Get progress summary:
   ```bash
   GET /api/progress/summary
   ```

2. Results show:
   - 45 quizzes taken
   - Average score: 78%
   - Topics covered: 12
   - Improvement trend: +15% over last month

3. View weak areas:
   - Quantum Entanglement: 60% avg
   - Error Correction: 55% avg

4. System generates focused content:
   ```bash
   GET /api/fetch/youtube/science?topic=quantum+entanglement
   ```

5. User studies weak topics

6. Retakes quizzes, score improves to 85%

---

## 8. Future Enhancements

### Planned Features

**AI-Powered Quiz Generation:**
- Use Gemini/Ollama to generate questions from papers
- Context-aware questions based on watched videos
- Adaptive difficulty based on performance

**Smart Recommendations:**
- ML model learns what content user engages with
- Personalized difficulty progression
- Topic dependency tracking (prerequisites)

**Spaced Repetition:**
- Integrate SRS (Spaced Repetition System)
- Schedule quiz reviews based on forgetting curve
- Optimize retention

**Social Features:**
- Share quiz results
- Compete on leaderboards
- Study groups with shared content

**Mobile App:**
- Take quizzes on phone
- Watch recommended videos
- Track progress on-the-go

---

## 9. Troubleshooting

**No content showing on dashboard?**
- Check if server is running: `curl http://localhost:5001/api/health`
- Check time block is active: `curl http://localhost:5001/api/schedule/current-block`
- Check console for errors: Open browser DevTools → Console

**Sample data instead of real content?**
- Add API keys to `.env` file
- Restart server after adding keys
- Check logs: `tail -f rfai.log`

**Quiz generation errors?**
- Check database initialized: `ls ~/.rfai/data/rfai.db`
- Check permissions: `chmod 755 ~/.rfai/data/rfai.db`
- Reinitialize: `python database/init_db.py`

**Perplexity not working?**
- Verify API key: `echo $PERPLEXITY_API_KEY`
- Check credits remaining on Perplexity dashboard
- Falls back to template mode if key missing

---

## 10. Summary

Your system now has:

✅ **Real Content Fetching**
- YouTube videos from real API
- ArXiv research papers
- IMDB movie recommendations

✅ **Study Plan Integration**
- Perplexity AI for personalized recommendations
- Content discovery from study goals

✅ **Progress Testing**
- Quiz generation for any topic
- Automatic grading and feedback
- Progress tracking across topics

✅ **Dashboard Integration**
- Automatic content display per time block
- Visual cards with thumbnails
- One-click access to resources

**Next Steps:**
1. Add API keys for real data
2. Use dashboard to explore content
3. Take quizzes after learning
4. Track progress monthly

**Documentation:**
- API Reference: [ACCESS_CONTROL_GUIDE.md](ACCESS_CONTROL_GUIDE.md)
- Setup Guide: [SETUP_GUIDE.md](../SETUP_GUIDE.md)
- Complete Features: [IMPLEMENTATION_COMPLETE.md](../IMPLEMENTATION_COMPLETE.md)

---

**Last Updated:** 2024-12-17
**Version:** 2.1
**Status:** ✅ Fully Operational
