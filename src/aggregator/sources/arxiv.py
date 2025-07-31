# src/aggregator/sources/arxiv.py

import requests
import feedparser
import time
from typing import List, Optional
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.paper import Paper
from ..utils.logger import setup_logger
from ..utils.helpers import clean_string, format_date

logger = setup_logger()

class ArxivClient:
    """
    Production-ready ArXiv API client with robust error handling and rate limiting.
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
        self.rate_limit_delay = 3  # seconds between requests as per ArXiv guidelines
        self.last_request_time = 0
    
    def _setup_session(self):
        """Configure session with retry strategy and timeouts."""
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        self.session.headers.update({
            'User-Agent': 'ResearchQuantize/1.1.0 (https://github.com/desenyon/ResearchQuantize)'
        })
    
    def _rate_limit(self):
        """Implement rate limiting to respect ArXiv's guidelines."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_papers(self, query: str, limit: int = 10, sort_by: str = "relevance") -> List[Paper]:
        """
        Fetch papers from ArXiv based on the query.
        
        Args:
            query (str): The search query.
            limit (int): Maximum number of papers to retrieve.
            sort_by (str): Sort order - 'relevance', 'lastUpdatedDate', 'submittedDate'
        
        Returns:
            List[Paper]: A list of Paper objects.
        """
        logger.info(f"Fetching papers from ArXiv for query: '{query}' (limit: {limit})")
        
        try:
            self._rate_limit()
            
            # Construct search query
            search_query = self._build_search_query(query)
            
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': min(limit, 200),  # ArXiv limit
                'sortBy': sort_by,
                'sortOrder': 'descending'
            }
            
            response = self.session.get(
                self.BASE_URL, 
                params=params, 
                timeout=30
            )
            response.raise_for_status()
            
            papers = self._parse_response(response.text)
            logger.info(f"Successfully fetched {len(papers)} papers from ArXiv")
            return papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from ArXiv: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in ArXiv client: {str(e)}")
            return []
    
    def _build_search_query(self, query: str) -> str:
        """
        Build a properly formatted ArXiv search query.
        
        Args:
            query (str): User's search query
            
        Returns:
            str: Formatted ArXiv query
        """
        # Clean the query
        query = clean_string(query)
        
        # For better results, search in title, abstract, and comments
        # Use 'all:' prefix for general search or specific fields
        if not any(prefix in query.lower() for prefix in ['ti:', 'au:', 'abs:', 'cat:', 'all:']):
            # If no field specified, search in title and abstract
            formatted_query = f'ti:"{query}" OR abs:"{query}"'
        else:
            formatted_query = query
        
        return formatted_query
    
    def _parse_response(self, xml_data: str) -> List[Paper]:
        """
        Parse the ArXiv API response using feedparser for robust XML handling.
        
        Args:
            xml_data (str): The XML response from ArXiv.
        
        Returns:
            List[Paper]: A list of Paper objects.
        """
        try:
            # Use feedparser for robust Atom feed parsing
            feed = feedparser.parse(xml_data)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"ArXiv feed parsing warning: {feed.bozo_exception}")
            
            papers = []
            
            for entry in feed.entries:
                try:
                    paper = self._parse_entry(entry)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Error parsing ArXiv entry: {str(e)}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"Error parsing ArXiv response: {str(e)}")
            return []
    
    def _parse_entry(self, entry) -> Optional[Paper]:
        """
        Parse a single ArXiv entry into a Paper object.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Optional[Paper]: Paper object or None if parsing fails
        """
        try:
            # Extract basic information
            title = clean_string(entry.get('title', ''))
            if not title:
                return None
            
            # Extract authors
            authors = []
            if hasattr(entry, 'authors'):
                for author in entry.authors:
                    if hasattr(author, 'name'):
                        authors.append(clean_string(author.name))
            elif hasattr(entry, 'author'):
                authors.append(clean_string(entry.author))
            
            # Extract dates
            published_date = entry.get('published', '')
            updated_date = entry.get('updated', '')
            
            # Extract abstract
            abstract = clean_string(entry.get('summary', ''))
            
            # Extract ArXiv ID and URL
            arxiv_id = None
            url = entry.get('id', '')
            if url:
                # Extract ArXiv ID from URL (e.g., http://arxiv.org/abs/1234.5678v1)
                import re
                id_match = re.search(r'arxiv\.org/abs/([0-9]+\.[0-9]+)', url)
                if id_match:
                    arxiv_id = id_match.group(1)
            
            # Extract PDF URL
            pdf_url = None
            if hasattr(entry, 'links'):
                for link in entry.links:
                    if link.get('type') == 'application/pdf':
                        pdf_url = link.get('href')
                        break
            
            # Extract categories (subject areas)
            categories = []
            if hasattr(entry, 'tags'):
                categories = [tag.get('term', '') for tag in entry.tags]
            
            # Extract DOI if available
            doi = None
            if hasattr(entry, 'arxiv_doi'):
                doi = entry.arxiv_doi
            
            # Create Paper object
            paper = Paper(
                title=title,
                authors=authors,
                published_date=published_date,
                source="ArXiv",
                abstract=abstract,
                url=url,
                doi=doi,
                keywords=categories,
                pdf_url=pdf_url,
                arxiv_id=arxiv_id
            )
            
            return paper
            
        except Exception as e:
            logger.warning(f"Error parsing ArXiv entry: {str(e)}")
            return None
    
    def search_by_category(self, category: str, limit: int = 10) -> List[Paper]:
        """
        Search papers by ArXiv category.
        
        Args:
            category (str): ArXiv category (e.g., 'cs.AI', 'physics.gen-ph')
            limit (int): Maximum number of papers
            
        Returns:
            List[Paper]: Papers in the specified category
        """
        query = f"cat:{category}"
        return self.fetch_papers(query, limit, sort_by="submittedDate")
    
    def search_by_author(self, author: str, limit: int = 10) -> List[Paper]:
        """
        Search papers by author name.
        
        Args:
            author (str): Author name
            limit (int): Maximum number of papers
            
        Returns:
            List[Paper]: Papers by the specified author
        """
        query = f'au:"{author}"'
        return self.fetch_papers(query, limit, sort_by="submittedDate")
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Paper]:
        """
        Get a specific paper by ArXiv ID.
        
        Args:
            arxiv_id (str): ArXiv ID (e.g., '1234.5678')
            
        Returns:
            Optional[Paper]: Paper object or None if not found
        """
        query = f"id:{arxiv_id}"
        papers = self.fetch_papers(query, limit=1)
        return papers[0] if papers else None
