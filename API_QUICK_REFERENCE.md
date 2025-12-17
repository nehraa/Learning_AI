# RFAI API Quick Reference

## Content Fetching Endpoints

### YouTube Videos
```bash
# Science videos
GET /api/fetch/youtube/science?max_results=10

# Self-help videos
GET /api/fetch/youtube/selfhelp?max_results=10
```

### Research Papers
```bash
# ArXiv papers
GET /api/fetch/papers?max_results=10
```

### Movies
```bash
# Movie recommendations
GET /api/fetch/movies?max_results=10
```

### Current Block Content
```bash
# Get content for active time block
GET /api/fetch/current-block-content
```

### Study Plan Recommendations
```bash
# Get AI recommendations from study plan
POST /api/fetch/study-plan-content
Content-Type: application/json

{
  "study_plan": "Your study goals here..."
}
```

## Quiz & Progress Endpoints

### Generate Quiz
```bash
POST /api/quiz/generate
Content-Type: application/json

{
  "topic": "Quantum Computing",
  "difficulty": "medium",
  "num_questions": 10
}
```

### Get Quiz
```bash
GET /api/quiz/<quiz_id>
```

### Submit Quiz
```bash
POST /api/quiz/<quiz_id>/submit
Content-Type: application/json

{
  "answers": {
    "q1": "a",
    "q2": "c",
    "q3": "b"
  }
}
```

### Progress Summary
```bash
# All topics
GET /api/progress/summary

# Specific topic
GET /api/progress/summary?topic=Quantum Computing
```

## Existing Endpoints (Still Available)

### Schedule
```bash
GET /api/schedule/current-block
GET /api/schedule/full-day
```

### Access Control
```bash
GET /api/access-control/check?content_type=movies
POST /api/activity/log-page
POST /api/activity/block-activity
```

### Attention Monitoring
```bash
GET /api/attention/current
GET /api/attention/history
GET /api/attention/signals
```

### Sessions
```bash
POST /api/time-blocks/session/start
POST /api/time-blocks/session/<id>/end
GET /api/analytics/session-activity/<id>
```

### System
```bash
GET /api/status
GET /api/health
GET /api/config
```

## Python Examples

### Fetch Content
```python
import requests

# Get science videos
response = requests.get('http://localhost:5001/api/fetch/youtube/science')
videos = response.json()['videos']

for video in videos:
    print(f"{video['title']} - {video['url']}")
```

### Generate & Take Quiz
```python
# Generate quiz
quiz = requests.post('http://localhost:5001/api/quiz/generate',
    json={'topic': 'Machine Learning', 'num_questions': 5}
).json()

# Submit answers
results = requests.post(
    f"http://localhost:5001/api/quiz/{quiz['quiz_id']}/submit",
    json={'answers': {'q1': 'a', 'q2': 'b', 'q3': 'a'}}
).json()

print(f"Score: {results['score_percentage']}%")
```

### Get Study Plan Recommendations
```python
study_plan = """
I want to learn:
1. Quantum Computing basics
2. Quantum algorithms
3. Quantum error correction
"""

recs = requests.post('http://localhost:5001/api/fetch/study-plan-content',
    json={'study_plan': study_plan}
).json()

print(recs['recommendations'])
```

## Dashboard URL

```
http://localhost:5001/static/dashboard_enhanced.html
```

## Testing Script

```bash
python test_content_and_progress.py
```

---

**Full Documentation:**
- [Content & Progress Guide](docs/CONTENT_PROGRESS_GUIDE.md)
- [Access Control Guide](docs/ACCESS_CONTROL_GUIDE.md)
- [Implementation Summary](IMPLEMENTATION_COMPLETE.md)
