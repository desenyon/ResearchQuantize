# src/aggregator/sources/semantic_scholar.py

import requests
import time
from typing import List, Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.paper import Paper
from ..utils.logger import setup_logger
from ..utils.helpers import clean_string, format_date

logger = setup_logger()

class SemanticScholarClient:
    """
    Production-ready Semantic Scholar API client with comprehensive features.
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self._setup_session()
        self.rate_limit_delay = 0.1  # 100ms between requests (free tier: 100 req/5min)
        self.last_request_time = 0
    
    def _setup_session(self):
        """Configure session with retry strategy and headers."""
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        headers = {
            'User-Agent': 'ResearchQuantize/1.1.0 (https://github.com/desenyon/ResearchQuantize)'
        }
        
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
        self.session.headers.update(headers)
    
    def _rate_limit(self):
        """Implement rate limiting to respect API limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_papers(self, query: str, limit: int = 10, year_filter: Optional[str] = None,
                    venue_filter: Optional[str] = None, field_filter: Optional[str] = None) -> List[Paper]:
        """
        Fetch papers from Semantic Scholar based on the query.
        
        Args:
            query (str): The search query.
            limit (int): Maximum number of papers to retrieve.
            year_filter (str): Year range filter (e.g., "2020-2023")
            venue_filter (str): Venue filter
            field_filter (str): Field of study filter
        
        Returns:
            List[Paper]: A list of Paper objects.
        """
        logger.info(f"Fetching papers from Semantic Scholar for query: '{query}' (limit: {limit})")
        
        try:
            self._rate_limit()
            
            # Build comprehensive field list for detailed paper info
            fields = [
                'title', 'authors', 'year', 'publicationDate', 'abstract',
                'url', 'venue', 'citationCount', 'referenceCount', 'fieldsOfStudy',
                'publicationTypes', 'publicationVenue', 'externalIds', 'openAccessPdf'
            ]
            
            params = {
                'query': query,
                'limit': min(limit, 100),  # API limit
                'fields': ','.join(fields)
            }
            
            # Add filters
            if year_filter:
                params['year'] = year_filter
            if venue_filter:
                params['venue'] = venue_filter
            if field_filter:
                params['fieldsOfStudy'] = field_filter
            
            response = self.session.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            papers = self._parse_response(data)
            logger.info(f"Successfully fetched {len(papers)} papers from Semantic Scholar")
            return papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Semantic Scholar: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Semantic Scholar client: {str(e)}")
            return []
    
    def _parse_response(self, data: Dict[str, Any]) -> List[Paper]:
        """
        Parse the Semantic Scholar API response and return a list of Paper objects.
        
        Args:
            data (dict): The JSON response from Semantic Scholar.
        
        Returns:
            List[Paper]: A list of Paper objects.
        """
        papers = []
        
        for paper_data in data.get('data', []):
            try:
                paper = self._parse_paper_data(paper_data)
                if paper:
                    papers.append(paper)
            except Exception as e:
                logger.warning(f"Error parsing Semantic Scholar paper: {str(e)}")
                continue
        
        return papers
    
    def _parse_paper_data(self, paper_data: Dict[str, Any]) -> Optional[Paper]:
        """
        Parse individual paper data into Paper object.
        
        Args:
            paper_data (dict): Individual paper data from API
            
        Returns:
            Optional[Paper]: Paper object or None if parsing fails
        """
        try:
            # Extract basic information
            title = clean_string(paper_data.get('title', ''))
            if not title:
                return None
            
            # Extract authors
            authors = []
            for author in paper_data.get('authors', []):
                if isinstance(author, dict) and 'name' in author:
                    authors.append(clean_string(author['name']))
                elif isinstance(author, str):
                    authors.append(clean_string(author))
            
            # Extract publication date
            published_date = paper_data.get('publicationDate') or paper_data.get('year')
            if published_date:
                published_date = str(published_date)
            
            # Extract abstract
            abstract = clean_string(paper_data.get('abstract', ''))
            
            # Extract URL
            url = paper_data.get('url', '')
            
            # Extract venue information
            venue = paper_data.get('venue', '')
            if not venue and paper_data.get('publicationVenue'):
                venue = paper_data['publicationVenue'].get('name', '')
            
            # Extract external IDs
            external_ids = paper_data.get('externalIds', {})
            doi = external_ids.get('DOI')
            arxiv_id = external_ids.get('ArXiv')
            pubmed_id = external_ids.get('PubMed')
            
            # Extract semantic scholar ID
            semantic_scholar_id = paper_data.get('paperId')
            
            # Extract citation count
            citations = paper_data.get('citationCount')
            
            # Extract fields of study as keywords
            keywords = paper_data.get('fieldsOfStudy', [])
            if keywords and isinstance(keywords, list):
                keywords = [clean_string(field) for field in keywords if field]
            
            # Extract PDF URL
            pdf_url = None
            if paper_data.get('openAccessPdf') and paper_data['openAccessPdf'].get('url'):
                pdf_url = paper_data['openAccessPdf']['url']
            
            # Create Paper object
            paper = Paper(
                title=title,
                authors=authors,
                published_date=published_date,
                source="Semantic Scholar",
                abstract=abstract,
                url=url,
                doi=doi,
                keywords=keywords,
                citations=citations,
                journal=venue,
                pdf_url=pdf_url,
                arxiv_id=arxiv_id,
                pubmed_id=pubmed_id,
                semantic_scholar_id=semantic_scholar_id
            )
            
            return paper
            
        except Exception as e:
            logger.warning(f"Error parsing Semantic Scholar paper data: {str(e)}")
            return None
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """
        Get a specific paper by Semantic Scholar ID.
        
        Args:
            paper_id (str): Semantic Scholar paper ID
            
        Returns:
            Optional[Paper]: Paper object or None if not found
        """
        try:
            self._rate_limit()
            
            fields = [
                'title', 'authors', 'year', 'publicationDate', 'abstract',
                'url', 'venue', 'citationCount', 'referenceCount', 'fieldsOfStudy',
                'publicationTypes', 'publicationVenue', 'externalIds', 'openAccessPdf'
            ]
            
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params={'fields': ','.join(fields)},
                timeout=30
            )
            response.raise_for_status()
            
            paper_data = response.json()
            return self._parse_paper_data(paper_data)
            
        except Exception as e:
            logger.error(f"Error fetching paper by ID from Semantic Scholar: {str(e)}")
            return None
    
    def search_by_author(self, author: str, limit: int = 10) -> List[Paper]:
        """
        Search papers by author name.
        
        Args:
            author (str): Author name
            limit (int): Maximum number of papers
            
        Returns:
            List[Paper]: Papers by the specified author
        """
        try:
            self._rate_limit()
            
            # First, search for the author
            author_response = self.session.get(
                f"{self.BASE_URL}/author/search",
                params={'query': author, 'limit': 1},
                timeout=30
            )
            author_response.raise_for_status()
            
            author_data = author_response.json()
            if not author_data.get('data'):
                return []
            
            author_id = author_data['data'][0]['authorId']
            
            # Get papers by author ID
            papers_response = self.session.get(
                f"{self.BASE_URL}/author/{author_id}/papers",
                params={
                    'limit': limit,
                    'fields': 'title,authors,year,publicationDate,abstract,url,venue,citationCount'
                },
                timeout=30
            )
            papers_response.raise_for_status()
            
            papers_data = papers_response.json()
            papers = []
            
            for paper_data in papers_data.get('data', []):
                paper = self._parse_paper_data(paper_data)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching by author in Semantic Scholar: {str(e)}")
            return []
    
    def get_trending_papers(self, field: str = "computer-science", limit: int = 10) -> List[Paper]:
        """
        Get trending papers in a specific field.
        
        Args:
            field (str): Field of study
            limit (int): Maximum number of papers
            
        Returns:
            List[Paper]: Trending papers
        """
        # Use recent highly-cited papers as proxy for trending
        current_year = 2025  # Based on context
        year_filter = f"{current_year-2}-{current_year}"
        
        return self.fetch_papers(
            query=f"fieldsOfStudy:{field}",
            limit=limit,
            year_filter=year_filter
        )