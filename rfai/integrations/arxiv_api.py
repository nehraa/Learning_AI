"""
ArXiv API Integration
Discovers academic papers based on learning topics and research interests
"""

import logging
import arxiv
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ArXivDiscovery:
    """
    ArXiv paper discovery using the arxiv Python library
    """
    
    def __init__(self):
        """Initialize ArXiv discovery client"""
        try:
            self.client = arxiv.Client()
            logger.info("ArXiv API initialized")
        except Exception as e:
            logger.error(f"Error initializing ArXiv client: {e}")
            self.client = None
    
    def search_papers(self, query: str, max_results: int = 10, 
                     categories: List[str] = None,
                     sort_by: str = 'relevance') -> List[Dict]:
        """
        Search for papers on ArXiv
        
        Args:
            query: Search query (e.g., "quantum entanglement")
            max_results: Max papers to return
            categories: ArXiv categories (e.g., ['quant-ph', 'cs.LG'])
            sort_by: 'relevance', 'lastUpdatedDate', 'submittedDate'
        
        Returns:
            List of paper dicts with metadata
        """
        if not self.client:
            logger.error("ArXiv client not initialized")
            return []
        
        try:
            # Build search query
            search_query = query
            if categories:
                # Add category filters
                cat_filters = " OR ".join([f"cat:{cat}" for cat in categories])
                search_query = f"({query}) AND ({cat_filters})"
            
            # Map sort_by to arxiv.SortCriterion
            sort_criterion = arxiv.SortCriterion.Relevance
            if sort_by == 'lastUpdatedDate':
                sort_criterion = arxiv.SortCriterion.LastUpdatedDate
            elif sort_by == 'submittedDate':
                sort_criterion = arxiv.SortCriterion.SubmittedDate
            
            # Create search
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=sort_criterion
            )
            
            papers = []
            for result in self.client.results(search):
                # Extract paper metadata
                paper = {
                    'id': f'arxiv_{result.entry_id.split("/")[-1]}',
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'type': 'paper',
                    'source': 'arxiv',
                    'title': result.title,
                    'abstract': result.summary,
                    'authors': [author.name for author in result.authors],
                    'primary_category': result.primary_category,
                    'categories': result.categories,
                    'published_date': result.published.strftime('%Y-%m-%d'),
                    'updated_date': result.updated.strftime('%Y-%m-%d'),
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'comment': result.comment,
                    'journal_ref': result.journal_ref,
                    'doi': result.doi,
                    'difficulty': self._estimate_difficulty(result)
                }
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers for query: {query}")
            return papers
        
        except Exception as e:
            logger.error(f"ArXiv search error: {e}")
            return []
    
    def _estimate_difficulty(self, result) -> str:
        """Estimate paper difficulty based on metadata"""
        title = result.title.lower()
        abstract = result.summary.lower()
        
        # Check for introductory/review papers
        intro_keywords = ['introduction', 'review', 'tutorial', 'survey', 'overview', 
                         'primer', 'basics', 'fundamentals']
        if any(keyword in title or keyword in abstract[:200] for keyword in intro_keywords):
            return 'beginner'
        
        # Check for advanced/technical papers
        advanced_keywords = ['advanced', 'novel', 'quantum field', 'renormalization',
                           'topological', 'non-perturbative', 'theoretical framework']
        if any(keyword in title or keyword in abstract[:200] for keyword in advanced_keywords):
            return 'advanced'
        
        # Check page count or length indicators
        if result.comment:
            comment = result.comment.lower()
            if 'pages' in comment:
                # Try to extract page count
                import re
                match = re.search(r'(\d+)\s*pages', comment)
                if match:
                    pages = int(match.group(1))
                    if pages < 10:
                        return 'beginner'
                    elif pages > 30:
                        return 'advanced'
        
        # Default to intermediate
        return 'intermediate'
    
    def search_by_topics(self, topics: List[str], max_per_topic: int = 3,
                        categories: List[str] = None) -> List[Dict]:
        """
        Search for papers across multiple topics
        
        Args:
            topics: List of research topics
            max_per_topic: Max papers per topic
            categories: ArXiv categories to filter by
        
        Returns:
            Combined list of papers
        """
        all_papers = []
        
        for topic in topics:
            papers = self.search_papers(
                query=topic,
                max_results=max_per_topic,
                categories=categories
            )
            all_papers.extend(papers)
        
        # Remove duplicates
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper['arxiv_id'] not in seen_ids:
                seen_ids.add(paper['arxiv_id'])
                unique_papers.append(paper)
        
        logger.info(f"Found {len(unique_papers)} unique papers across topics")
        return unique_papers
    
    def get_recent_papers(self, category: str, days_back: int = 7,
                         max_results: int = 10) -> List[Dict]:
        """
        Get recent papers in a category
        
        Args:
            category: ArXiv category (e.g., 'quant-ph')
            days_back: How many days back to search
            max_results: Max papers to return
        
        Returns:
            List of recent papers
        """
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=days_back)
        date_str = date_threshold.strftime('%Y%m%d')
        
        # Search with date filter
        query = f"cat:{category} AND submittedDate:[{date_str}0000 TO 99991231]"
        
        return self.search_papers(
            query=query,
            max_results=max_results,
            sort_by='submittedDate'
        )
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        Get a specific paper by ArXiv ID
        
        Args:
            arxiv_id: ArXiv paper ID (e.g., '2301.12345')
        
        Returns:
            Paper dict or None if not found
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search))
            
            return {
                'id': f'arxiv_{result.entry_id.split("/")[-1]}',
                'arxiv_id': result.entry_id.split('/')[-1],
                'type': 'paper',
                'source': 'arxiv',
                'title': result.title,
                'abstract': result.summary,
                'authors': [author.name for author in result.authors],
                'published_date': result.published.strftime('%Y-%m-%d'),
                'url': result.entry_id,
                'pdf_url': result.pdf_url
            }
        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {e}")
            return None


if __name__ == "__main__":
    # Test ArXiv integration
    logging.basicConfig(level=logging.INFO)
    
    arxiv_api = ArXivDiscovery()
    
    # Test search
    papers = arxiv_api.search_papers("quantum entanglement", max_results=3)
    print(f"\n✅ Found {len(papers)} papers")
    for paper in papers:
        print(f"  - {paper['title'][:60]}...")
        print(f"    Authors: {', '.join(paper['authors'][:3])}")
        print(f"    Difficulty: {paper['difficulty']}")
        print()
    
    # Test category search
    recent = arxiv_api.get_recent_papers("quant-ph", days_back=7, max_results=2)
    print(f"\n✅ Recent papers in quant-ph: {len(recent)}")
    for paper in recent:
        print(f"  - {paper['title'][:60]}...")
