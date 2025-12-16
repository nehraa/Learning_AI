"""
Notion API Integration
Access and sync learning notes from Notion databases
"""

import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NotionIntegration:
    """
    Notion API integration for accessing learning notes and databases
    """
    
    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion integration
        
        Args:
            api_key: Notion integration token
            database_id: Default database ID for learning notes
        """
        self.api_key = api_key or os.environ.get('NOTION_API_KEY')
        self.database_id = database_id or os.environ.get('NOTION_DATABASE_ID')
        self.base_url = "https://api.notion.com/v1"
        self.version = "2022-06-28"  # Notion API version
        
        if not self.api_key:
            logger.warning("No Notion API key - functionality disabled")
        else:
            logger.info("Notion API initialized")
    
    def _get_headers(self) -> Dict:
        """Get request headers"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': self.version
        }
    
    def query_database(self, database_id: Optional[str] = None,
                      filter_dict: Optional[Dict] = None,
                      sorts: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Query a Notion database
        
        Args:
            database_id: Database ID (uses default if not provided)
            filter_dict: Filter criteria
            sorts: Sort criteria
        
        Returns:
            List of pages
        """
        if not self.api_key:
            logger.error("Notion API key not configured")
            return []
        
        db_id = database_id or self.database_id
        if not db_id:
            logger.error("No database ID provided")
            return []
        
        try:
            url = f"{self.base_url}/databases/{db_id}/query"
            
            payload = {}
            if filter_dict:
                payload['filter'] = filter_dict
            if sorts:
                payload['sorts'] = sorts
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('results', [])
            
            logger.info(f"Retrieved {len(pages)} pages from Notion database")
            return pages
        
        except Exception as e:
            logger.error(f"Notion query error: {e}")
            return []
    
    def get_page(self, page_id: str) -> Optional[Dict]:
        """
        Get a Notion page
        
        Args:
            page_id: Page ID
        
        Returns:
            Page data
        """
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/pages/{page_id}"
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Get page error: {e}")
            return None
    
    def get_page_content(self, page_id: str) -> str:
        """
        Get page content (blocks)
        
        Args:
            page_id: Page ID
        
        Returns:
            Page content as text
        """
        if not self.api_key:
            return ""
        
        try:
            url = f"{self.base_url}/blocks/{page_id}/children"
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            blocks = data.get('results', [])
            
            # Extract text from blocks
            content = []
            for block in blocks:
                block_type = block.get('type')
                
                if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3']:
                    rich_text = block.get(block_type, {}).get('rich_text', [])
                    text = ''.join([t.get('plain_text', '') for t in rich_text])
                    if text:
                        content.append(text)
                
                elif block_type in ['bulleted_list_item', 'numbered_list_item']:
                    rich_text = block.get(block_type, {}).get('rich_text', [])
                    text = ''.join([t.get('plain_text', '') for t in rich_text])
                    if text:
                        content.append(f"• {text}")
            
            return '\n\n'.join(content)
        
        except Exception as e:
            logger.error(f"Get content error: {e}")
            return ""
    
    def get_learning_notes(self, topic: Optional[str] = None,
                          tag: Optional[str] = None) -> List[Dict]:
        """
        Get learning notes from Notion
        
        Args:
            topic: Filter by topic
            tag: Filter by tag
        
        Returns:
            List of note dicts
        """
        filters = None
        
        # Build filters
        if topic:
            filters = {
                'property': 'Topic',
                'rich_text': {
                    'contains': topic
                }
            }
        elif tag:
            filters = {
                'property': 'Tags',
                'multi_select': {
                    'contains': tag
                }
            }
        
        # Sort by last edited
        sorts = [
            {
                'property': 'Last edited time',
                'direction': 'descending'
            }
        ]
        
        pages = self.query_database(filter_dict=filters, sorts=sorts)
        
        # Extract note data
        notes = []
        for page in pages:
            props = page.get('properties', {})
            
            # Extract title
            title_prop = props.get('Name', {}).get('title', [])
            title = title_prop[0].get('plain_text', 'Untitled') if title_prop else 'Untitled'
            
            # Extract tags
            tags_prop = props.get('Tags', {}).get('multi_select', [])
            tags = [tag.get('name') for tag in tags_prop]
            
            # Get content
            content = self.get_page_content(page['id'])
            
            notes.append({
                'id': f'notion_{page["id"]}',
                'notion_id': page['id'],
                'type': 'note',
                'source': 'notion',
                'title': title,
                'content': content,
                'tags': tags,
                'created_time': page.get('created_time'),
                'last_edited_time': page.get('last_edited_time'),
                'url': page.get('url')
            })
        
        logger.info(f"Retrieved {len(notes)} notes from Notion")
        return notes
    
    def create_note(self, title: str, content: str, tags: List[str] = None) -> Optional[str]:
        """
        Create a new note in Notion
        
        Args:
            title: Note title
            content: Note content
            tags: Tags to add
        
        Returns:
            Page ID if successful
        """
        if not self.api_key or not self.database_id:
            logger.error("Notion not configured for creating notes")
            return None
        
        try:
            url = f"{self.base_url}/pages"
            
            # Build properties
            properties = {
                'Name': {
                    'title': [
                        {
                            'text': {
                                'content': title
                            }
                        }
                    ]
                }
            }
            
            if tags:
                properties['Tags'] = {
                    'multi_select': [
                        {'name': tag} for tag in tags
                    ]
                }
            
            # Build content blocks
            children = []
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    children.append({
                        'object': 'block',
                        'type': 'paragraph',
                        'paragraph': {
                            'rich_text': [
                                {
                                    'type': 'text',
                                    'text': {
                                        'content': paragraph
                                    }
                                }
                            ]
                        }
                    })
            
            payload = {
                'parent': {
                    'database_id': self.database_id
                },
                'properties': properties,
                'children': children
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            page_id = data.get('id')
            
            logger.info(f"Created Notion page: {page_id}")
            return page_id
        
        except Exception as e:
            logger.error(f"Create note error: {e}")
            return None
    
    def search(self, query: str) -> List[Dict]:
        """
        Search across Notion workspace
        
        Args:
            query: Search query
        
        Returns:
            List of matching pages
        """
        if not self.api_key:
            return []
        
        try:
            url = f"{self.base_url}/search"
            
            payload = {
                'query': query,
                'sort': {
                    'direction': 'descending',
                    'timestamp': 'last_edited_time'
                }
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            logger.info(f"Found {len(results)} pages for query: {query}")
            return results
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []


if __name__ == "__main__":
    # Test Notion API
    logging.basicConfig(level=logging.INFO)
    
    notion = NotionIntegration()
    
    if notion.api_key:
        print("✅ Notion API configured")
        
        if notion.database_id:
            notes = notion.get_learning_notes()
            print(f"\nRetrieved {len(notes)} notes")
            for note in notes[:3]:
                print(f"  - {note['title']}")
        else:
            print("⚠️  No database ID configured")
            print("Set NOTION_DATABASE_ID environment variable")
    else:
        print("❌ Notion API key not configured")
        print("Set NOTION_API_KEY environment variable")
        print("Get key from: https://www.notion.so/my-integrations")
