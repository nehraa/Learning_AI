"""
EdX Course Integration
Discovers and manages online courses from edX and similar platforms
"""

import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class EdXDiscovery:
    """
    EdX course discovery and management
    
    Note: EdX doesn't have a public API for course search, so this uses
    a curated database of courses with filtering capabilities.
    """
    
    def __init__(self):
        """Initialize EdX discovery with curated course database"""
        self.courses = self._load_course_database()
        logger.info(f"EdX integration initialized with {len(self.courses)} courses")
    
    def _load_course_database(self) -> List[Dict]:
        """
        Load curated database of edX courses
        
        This is a static database that should be updated periodically.
        In a production system, this could be loaded from a JSON file
        or updated via web scraping (with appropriate permissions).
        """
        return [
            # Computer Science & Programming
            {
                'id': 'edx_cs50p',
                'type': 'course',
                'source': 'edx',
                'title': "CS50's Introduction to Programming with Python",
                'provider': 'Harvard University',
                'url': 'https://www.edx.org/course/cs50s-introduction-to-programming-with-python',
                'subject': 'Computer Science',
                'topics': ['Python', 'Programming', 'Computer Science'],
                'difficulty': 'beginner',
                'duration_weeks': 10,
                'hours_per_week': '6-9',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'An introduction to programming using Python, for students with or without prior programming experience.'
            },
            {
                'id': 'edx_mit_6002x',
                'type': 'course',
                'source': 'edx',
                'title': 'Introduction to Computational Thinking and Data Science',
                'provider': 'MIT',
                'url': 'https://www.edx.org/course/introduction-to-computational-thinking-and-data-science',
                'subject': 'Computer Science',
                'topics': ['Python', 'Data Science', 'Computational Thinking'],
                'difficulty': 'intermediate',
                'duration_weeks': 9,
                'hours_per_week': '14-16',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'Learn how to use computation to accomplish a variety of goals and provides a brief introduction to data science.'
            },
            
            # Machine Learning & AI
            {
                'id': 'edx_mit_ml',
                'type': 'course',
                'source': 'edx',
                'title': 'Machine Learning with Python: from Linear Models to Deep Learning',
                'provider': 'MIT',
                'url': 'https://www.edx.org/course/machine-learning-with-python-from-linear-models-to',
                'subject': 'Machine Learning',
                'topics': ['Machine Learning', 'Python', 'Deep Learning', 'Neural Networks'],
                'difficulty': 'advanced',
                'duration_weeks': 15,
                'hours_per_week': '10-14',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'An in-depth introduction to the field of machine learning, from linear models to deep learning and reinforcement learning.'
            },
            {
                'id': 'edx_columbia_ai',
                'type': 'course',
                'source': 'edx',
                'title': 'Artificial Intelligence (AI)',
                'provider': 'Columbia University',
                'url': 'https://www.edx.org/course/artificial-intelligence-ai',
                'subject': 'Artificial Intelligence',
                'topics': ['AI', 'Search Algorithms', 'Game Playing', 'Logic'],
                'difficulty': 'intermediate',
                'duration_weeks': 12,
                'hours_per_week': '8-10',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'Learn the fundamentals of Artificial Intelligence (AI), and apply them to solve real-world problems.'
            },
            
            # Physics & Quantum Mechanics
            {
                'id': 'edx_mit_quantum',
                'type': 'course',
                'source': 'edx',
                'title': 'Quantum Mechanics for Everyone',
                'provider': 'Georgetown University',
                'url': 'https://www.edx.org/course/quantum-mechanics-for-everyone',
                'subject': 'Physics',
                'topics': ['Quantum Mechanics', 'Physics', 'Quantum Computing'],
                'difficulty': 'beginner',
                'duration_weeks': 8,
                'hours_per_week': '4-6',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'An introduction to quantum mechanics without the heavy mathematics, accessible to everyone.'
            },
            {
                'id': 'edx_mit_8370x',
                'type': 'course',
                'source': 'edx',
                'title': 'Quantum Information Science I',
                'provider': 'MIT',
                'url': 'https://www.edx.org/course/quantum-information-science-i',
                'subject': 'Physics',
                'topics': ['Quantum Computing', 'Quantum Information', 'Linear Algebra'],
                'difficulty': 'advanced',
                'duration_weeks': 12,
                'hours_per_week': '10-12',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'Learn the fundamentals of quantum information science including quantum computation and quantum communication.'
            },
            
            # Biology & Chemistry
            {
                'id': 'edx_mit_bio',
                'type': 'course',
                'source': 'edx',
                'title': 'Introduction to Biology - The Secret of Life',
                'provider': 'MIT',
                'url': 'https://www.edx.org/course/introduction-to-biology-the-secret-of-life',
                'subject': 'Biology',
                'topics': ['Biology', 'Genetics', 'Molecular Biology'],
                'difficulty': 'beginner',
                'duration_weeks': 16,
                'hours_per_week': '10-16',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'Explore the secret of life through biochemistry, genetics, molecular biology, and more.'
            },
            {
                'id': 'edx_rice_chemistry',
                'type': 'course',
                'source': 'edx',
                'title': 'Principles of Organic Chemistry',
                'provider': 'Rice University',
                'url': 'https://www.edx.org/course/principles-of-organic-chemistry',
                'subject': 'Chemistry',
                'topics': ['Organic Chemistry', 'Chemical Reactions', 'Molecular Structure'],
                'difficulty': 'intermediate',
                'duration_weeks': 15,
                'hours_per_week': '8-10',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'Learn organic chemistry principles including structure, bonding, and reactivity.'
            },
            
            # Neuroscience
            {
                'id': 'edx_harvard_neuro',
                'type': 'course',
                'source': 'edx',
                'title': 'Fundamentals of Neuroscience',
                'provider': 'Harvard University',
                'url': 'https://www.edx.org/course/fundamentals-of-neuroscience',
                'subject': 'Neuroscience',
                'topics': ['Neuroscience', 'Brain', 'Neurons', 'Cognition'],
                'difficulty': 'beginner',
                'duration_weeks': 15,
                'hours_per_week': '4-6',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'Learn about the nervous system, how it functions, and how neuroscience can explain our behavior.'
            },
            {
                'id': 'edx_mit_compneuro',
                'type': 'course',
                'source': 'edx',
                'title': 'Computational Neuroscience',
                'provider': 'University of Washington',
                'url': 'https://www.edx.org/course/computational-neuroscience',
                'subject': 'Neuroscience',
                'topics': ['Computational Neuroscience', 'Neural Networks', 'Brain Models'],
                'difficulty': 'advanced',
                'duration_weeks': 10,
                'hours_per_week': '8-10',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'Learn how to model neurons and neural circuits using mathematical and computational techniques.'
            },
            
            # Mathematics & Statistics
            {
                'id': 'edx_mit_calculus',
                'type': 'course',
                'source': 'edx',
                'title': 'Calculus 1A: Differentiation',
                'provider': 'MIT',
                'url': 'https://www.edx.org/course/calculus-1a-differentiation',
                'subject': 'Mathematics',
                'topics': ['Calculus', 'Differentiation', 'Mathematics'],
                'difficulty': 'intermediate',
                'duration_weeks': 13,
                'hours_per_week': '6-10',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'Learn differential calculus from one of the world\'s leading universities.'
            },
            {
                'id': 'edx_mit_stats',
                'type': 'course',
                'source': 'edx',
                'title': 'Introduction to Probability and Statistics',
                'provider': 'MIT',
                'url': 'https://www.edx.org/course/introduction-to-probability-and-statistics',
                'subject': 'Statistics',
                'topics': ['Probability', 'Statistics', 'Data Analysis'],
                'difficulty': 'intermediate',
                'duration_weeks': 16,
                'hours_per_week': '12-16',
                'format': 'self-paced',
                'cost': 'free (certificate: paid)',
                'description': 'An introduction to probabilistic models and inference, and their application to data analysis.'
            }
        ]
    
    def search_courses(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for courses by keyword
        
        Args:
            query: Search query (matches title, topics, description)
            max_results: Max courses to return
        
        Returns:
            List of matching courses
        """
        query_lower = query.lower()
        matches = []
        
        for course in self.courses:
            # Check if query matches title, topics, or description
            if (query_lower in course['title'].lower() or
                any(query_lower in topic.lower() for topic in course['topics']) or
                query_lower in course['description'].lower() or
                query_lower in course['subject'].lower()):
                matches.append(course)
        
        logger.info(f"Found {len(matches)} courses matching: {query}")
        return matches[:max_results]
    
    def get_by_subject(self, subject: str, max_results: int = 10) -> List[Dict]:
        """Get courses by subject area"""
        subject_lower = subject.lower()
        matches = [c for c in self.courses if subject_lower in c['subject'].lower()]
        return matches[:max_results]
    
    def get_by_difficulty(self, difficulty: str) -> List[Dict]:
        """Get courses by difficulty level"""
        return [c for c in self.courses if c['difficulty'] == difficulty]
    
    def get_by_topics(self, topics: List[str], max_per_topic: int = 3) -> List[Dict]:
        """
        Get courses across multiple topics
        
        Args:
            topics: List of topic keywords
            max_per_topic: Max courses per topic
        
        Returns:
            Combined list of courses
        """
        all_courses = []
        
        for topic in topics:
            courses = self.search_courses(topic, max_results=max_per_topic)
            all_courses.extend(courses)
        
        # Remove duplicates
        seen_ids = set()
        unique_courses = []
        for course in all_courses:
            if course['id'] not in seen_ids:
                seen_ids.add(course['id'])
                unique_courses.append(course)
        
        logger.info(f"Found {len(unique_courses)} unique courses across topics")
        return unique_courses
    
    def recommend_by_interests(self, interests: List[str], 
                               difficulty: Optional[str] = None,
                               max_results: int = 5) -> List[Dict]:
        """
        Recommend courses based on user interests
        
        Args:
            interests: List of interest keywords
            difficulty: Optional difficulty filter
            max_results: Max courses to return
        
        Returns:
            Recommended courses
        """
        # Score each course based on interest match
        scored_courses = []
        
        for course in self.courses:
            score = 0
            for interest in interests:
                interest_lower = interest.lower()
                # Higher score for exact topic match
                if any(interest_lower in topic.lower() for topic in course['topics']):
                    score += 3
                # Medium score for title match
                if interest_lower in course['title'].lower():
                    score += 2
                # Lower score for description match
                if interest_lower in course['description'].lower():
                    score += 1
            
            if score > 0:
                scored_courses.append((score, course))
        
        # Sort by score (descending)
        scored_courses.sort(key=lambda x: x[0], reverse=True)
        
        # Filter by difficulty if specified
        if difficulty:
            scored_courses = [(s, c) for s, c in scored_courses if c['difficulty'] == difficulty]
        
        # Return top courses
        recommended = [course for score, course in scored_courses[:max_results]]
        logger.info(f"Recommended {len(recommended)} courses based on interests")
        return recommended


if __name__ == "__main__":
    # Test EdX integration
    logging.basicConfig(level=logging.INFO)
    
    edx = EdXDiscovery()
    
    # Test search
    courses = edx.search_courses("quantum", max_results=3)
    print(f"\n✅ Found {len(courses)} courses for 'quantum'")
    for course in courses:
        print(f"  - {course['title']}")
        print(f"    Provider: {course['provider']}")
        print(f"    Difficulty: {course['difficulty']}")
        print()
    
    # Test recommendations
    interests = ["Machine Learning", "Python", "AI"]
    recommended = edx.recommend_by_interests(interests, max_results=3)
    print(f"\n✅ Recommended courses for {interests}")
    for course in recommended:
        print(f"  - {course['title']}")
