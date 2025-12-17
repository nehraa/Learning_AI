from app import EnhancedSystem
import json

s = EnhancedSystem()
print('courses:', len(s.course_discovery.courses))
print(json.dumps(s.course_discovery.search_courses('python', 3, vector_store=s.vector_store), indent=2))
