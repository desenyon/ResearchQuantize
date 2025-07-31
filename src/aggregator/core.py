# src/aggregator/core.py

import asyncio
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .sources.arxiv import ArxivClient
from .sources.pubmed import PubmedClient
from .sources.semantic_scholar import SemanticScholarClient
from .models.paper import Paper
from .utils.logger import setup_logger
from .utils.helpers import deduplicate_papers, merge_papers_by_similarity

logger = setup_logger()

class PaperAggregator:
    """Advanced paper aggregation engine with parallel processing and deduplication."""
    
    def __init__(self):
        self.clients = {
            'arxiv': ArxivClient(),
            'pubmed': PubmedClient(),
            'semantic_scholar': SemanticScholarClient(),
        }
        self.max_workers = 4
    
    def aggregate_papers_parallel(self, query: str, limit: int = 10, 
                                sources: Optional[List[str]] = None,
                                enable_deduplication: bool = True) -> List[Paper]:
        """
        Aggregate papers from multiple sources in parallel with advanced features.
        
        Args:
            query (str): The search query.
            limit (int): Maximum number of papers to retrieve from each source.
            sources (List[str]): Specific sources to search. If None, searches all.
            enable_deduplication (bool): Whether to remove duplicate papers.
        
        Returns:
            List[Paper]: A list of aggregated and deduplicated Paper objects.
        """
        start_time = time.time()
        logger.info(f"Starting parallel aggregation for query: '{query}' with limit: {limit}")
        
        # Determine which sources to use
        active_sources = sources or list(self.clients.keys())
        active_clients = {name: client for name, client in self.clients.items() 
                         if name in active_sources}
        
        all_papers = []
        source_stats = {}
        
        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks for each source
            future_to_source = {
                executor.submit(self._fetch_from_source, name, client, query, limit): name
                for name, client in active_clients.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    papers = future.result(timeout=30)  # 30 second timeout per source
                    all_papers.extend(papers)
                    source_stats[source_name] = len(papers)
                    logger.info(f"Retrieved {len(papers)} papers from {source_name}")
                except Exception as e:
                    logger.error(f"Error fetching from {source_name}: {str(e)}")
                    source_stats[source_name] = 0
        
        # Deduplicate papers if enabled
        if enable_deduplication and all_papers:
            original_count = len(all_papers)
            all_papers = deduplicate_papers(all_papers)
            dedup_count = len(all_papers)
            logger.info(f"Deduplication: {original_count} -> {dedup_count} papers "
                       f"({original_count - dedup_count} duplicates removed)")
        
        end_time = time.time()
        logger.info(f"Aggregation completed in {end_time - start_time:.2f} seconds. "
                   f"Total papers: {len(all_papers)}")
        logger.info(f"Source breakdown: {source_stats}")
        
        return all_papers
    
    def _fetch_from_source(self, source_name: str, client, query: str, limit: int) -> List[Paper]:
        """
        Fetch papers from a single source with error handling.
        
        Args:
            source_name (str): Name of the source
            client: The client instance for the source
            query (str): Search query
            limit (int): Maximum papers to fetch
            
        Returns:
            List[Paper]: Papers from this source
        """
        try:
            return client.fetch_papers(query, limit)
        except Exception as e:
            logger.error(f"Failed to fetch from {source_name}: {str(e)}")
            return []

# Legacy function for backward compatibility
def aggregate_papers(query: str, limit: int = 10, sources: Optional[List[str]] = None) -> List[Paper]:
    """
    Legacy aggregation function - maintains backward compatibility.
    
    Args:
        query (str): The search query.
        limit (int): Maximum number of papers to retrieve from each source.
        sources (List[str]): Specific sources to search.
    
    Returns:
        List[Paper]: A list of aggregated Paper objects.
    """
    aggregator = PaperAggregator()
    return aggregator.aggregate_papers_parallel(query, limit, sources)