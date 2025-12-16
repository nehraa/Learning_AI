"""
Multi-Source Content Discovery
Integrates ArXiv, EdX, YouTube, IMDB, Perplexity, and Notion for comprehensive content recommendations
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class MultiSourceDiscovery:
    """
    Discovers learning content from multiple sources in parallel
    Sources: ArXiv, EdX, YouTube, IMDB, Perplexity, Notion
    """
    
    def __init__(self):
        """Initialize all discovery sources"""
        self.sources = {}
        
        # Try to initialize each source
        self._init_youtube()
        self._init_perplexity()
        self._init_imdb()
        self._init_notion()
        
        # ArXiv and EdX are already in the existing Learning_AI system
        logger.info(f"Initialized {len(self.sources)} content sources")
    
    def _init_youtube(self):
        """Initialize YouTube discovery"""
        try:
            from rfai.integrations.youtube_api import YouTubeDiscovery
            yt = YouTubeDiscovery()
            if yt.api_key:
                self.sources['youtube'] = yt
                logger.info("✓ YouTube API ready")
            else:
                logger.info("○ YouTube API not configured (optional)")
        except Exception as e:
            logger.debug(f"YouTube init failed: {e}")
    
    def _init_perplexity(self):
        """Initialize Perplexity search"""
        try:
            from rfai.integrations.perplexity_api import PerplexitySearch
            perp = PerplexitySearch()
            if perp.api_key:
                self.sources['perplexity'] = perp
                logger.info("✓ Perplexity API ready")
            else:
                logger.info("○ Perplexity API not configured (optional)")
        except Exception as e:
            logger.debug(f"Perplexity init failed: {e}")
    
    def _init_imdb(self):
        """Initialize IMDB/OMDb discovery"""
        try:
            from rfai.integrations.imdb_api import IMDBDiscovery
            imdb = IMDBDiscovery()
            if imdb.api_key:
                self.sources['imdb'] = imdb
                logger.info("✓ IMDB/OMDb API ready")
            else:
                logger.info("○ IMDB/OMDb API not configured (optional)")
        except Exception as e:
            logger.debug(f"IMDB init failed: {e}")
    
    def _init_notion(self):
        """Initialize Notion integration"""
        try:
            from rfai.integrations.notion_api import NotionIntegration
            notion = NotionIntegration()
            if notion.api_key:
                self.sources['notion'] = notion
                logger.info("✓ Notion API ready")
            else:
                logger.info("○ Notion API not configured (optional)")
        except Exception as e:
            logger.debug(f"Notion init failed: {e}")
    
    def discover_all(self, topic: str, subtopics: List[str] = None,
                    max_per_source: int = 5) -> Dict[str, List[Dict]]:
        """
        Discover content from all sources in parallel
        
        Args:
            topic: Main topic
            subtopics: Optional subtopics
            max_per_source: Max items per source
        
        Returns:
            Dict mapping source_name -> list of content items
        """
        results = {}
        
        # Use thread pool for parallel discovery
        with ThreadPoolExecutor(max_workers=len(self.sources)) as executor:
            futures = {}
            
            # Submit discovery tasks
            if 'youtube' in self.sources:
                futures[executor.submit(
                    self._discover_youtube, topic, subtopics, max_per_source
                )] = 'youtube'
            
            if 'perplexity' in self.sources:
                futures[executor.submit(
                    self._discover_perplexity, topic, max_per_source
                )] = 'perplexity'
            
            if 'imdb' in self.sources:
                futures[executor.submit(
                    self._discover_imdb, topic, max_per_source
                )] = 'imdb'
            
            if 'notion' in self.sources:
                futures[executor.submit(
                    self._discover_notion, topic, max_per_source
                )] = 'notion'
            
            # Collect results as they complete
            for future in as_completed(futures):
                source = futures[future]
                try:
                    items = future.result(timeout=30)
                    results[source] = items
                    logger.info(f"✓ {source}: {len(items)} items")
                except Exception as e:
                    logger.error(f"✗ {source} discovery failed: {e}")
                    results[source] = []
        
        return results
    
    def _discover_youtube(self, topic: str, subtopics: List[str], 
                         max_results: int) -> List[Dict]:
        """Discover YouTube videos"""
        yt = self.sources.get('youtube')
        if not yt:
            return []
        
        return yt.search_by_topic(topic, subtopics, max_per_topic=max_results)
    
    def _discover_perplexity(self, topic: str, max_results: int) -> List[Dict]:
        """Discover resources via Perplexity"""
        perp = self.sources.get('perplexity')
        if not perp:
            return []
        
        # Try multiple resource types
        all_resources = []
        for resource_type in ['tutorial', 'article', 'documentation']:
            resources = perp.find_resources(topic, resource_type)
            all_resources.extend(resources[:max_results // 3])
        
        return all_resources[:max_results]
    
    def _discover_imdb(self, topic: str, max_results: int) -> List[Dict]:
        """Discover educational movies/documentaries"""
        imdb = self.sources.get('imdb')
        if not imdb:
            return []
        
        return imdb.find_educational_content(topic)[:max_results]
    
    def _discover_notion(self, topic: str, max_results: int) -> List[Dict]:
        """Discover notes from Notion"""
        notion = self.sources.get('notion')
        if not notion:
            return []
        
        return notion.get_learning_notes(topic=topic)[:max_results]
    
    def get_all_content(self, topic: str, subtopics: List[str] = None) -> List[Dict]:
        """
        Get all content as a flat list
        
        Args:
            topic: Main topic
            subtopics: Optional subtopics
        
        Returns:
            Flat list of all content items
        """
        results = self.discover_all(topic, subtopics)
        
        all_content = []
        for source, items in results.items():
            all_content.extend(items)
        
        logger.info(f"Total: {len(all_content)} items from {len(results)} sources")
        return all_content
    
    def get_mixed_recommendations(self, topic: str, subtopics: List[str] = None,
                                  total: int = 10) -> List[Dict]:
        """
        Get mixed recommendations with diversity across sources
        
        Args:
            topic: Main topic
            subtopics: Optional subtopics
            total: Total recommendations to return
        
        Returns:
            Mixed list of recommendations
        """
        results = self.discover_all(topic, subtopics, max_per_source=total)
        
        # Round-robin selection for diversity
        mixed = []
        source_lists = list(results.values())
        
        while len(mixed) < total and any(source_lists):
            for source_list in source_lists:
                if source_list and len(mixed) < total:
                    mixed.append(source_list.pop(0))
        
        logger.info(f"Mixed recommendations: {len(mixed)} items")
        return mixed
    
    def search_specific_source(self, source: str, query: str, 
                              **kwargs) -> List[Dict]:
        """
        Search a specific source
        
        Args:
            source: Source name ('youtube', 'perplexity', 'imdb', 'notion')
            query: Search query
            **kwargs: Source-specific parameters
        
        Returns:
            List of results
        """
        if source not in self.sources:
            logger.warning(f"Source {source} not available")
            return []
        
        source_obj = self.sources[source]
        
        try:
            if source == 'youtube':
                return source_obj.search_videos(query, **kwargs)
            elif source == 'perplexity':
                result = source_obj.search(query, **kwargs)
                return [result] if result.get('answer') else []
            elif source == 'imdb':
                return source_obj.search_movies(query, **kwargs)
            elif source == 'notion':
                return source_obj.search(query, **kwargs)
        except Exception as e:
            logger.error(f"Search error in {source}: {e}")
            return []
    
    def get_available_sources(self) -> List[str]:
        """Get list of available sources"""
        return list(self.sources.keys())


if __name__ == "__main__":
    # Test multi-source discovery
    logging.basicConfig(level=logging.INFO)
    
    discovery = MultiSourceDiscovery()
    
    print(f"\n{'='*60}")
    print(f"Available sources: {', '.join(discovery.get_available_sources())}")
    print(f"{'='*60}\n")
    
    if discovery.sources:
        # Test discovery
        print("Testing discovery for 'machine learning'...")
        results = discovery.discover_all("machine learning", max_per_source=3)
        
        for source, items in results.items():
            print(f"\n{source.upper()}: {len(items)} items")
            for i, item in enumerate(items[:2], 1):
                title = item.get('title', item.get('name', 'No title'))
                print(f"  {i}. {title[:60]}...")
    else:
        print("No sources configured. Set API keys:")
        print("  - YOUTUBE_API_KEY")
        print("  - PERPLEXITY_API_KEY")
        print("  - OMDB_API_KEY")
        print("  - NOTION_API_KEY + NOTION_DATABASE_ID")
