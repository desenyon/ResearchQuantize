from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from .models.paper import Paper
from .sources import ArxivClient, BaseSourceClient, PubmedClient, SemanticScholarClient
from .utils.helpers import deduplicate_papers, parse_year
from .utils.logger import setup_logger

logger = setup_logger(__name__)


def _default_clients() -> Dict[str, BaseSourceClient]:
    return {
        "arxiv": ArxivClient(),
        "pubmed": PubmedClient(),
        "semantic_scholar": SemanticScholarClient(),
    }


@dataclass
class AggregationStats:
    by_source: Dict[str, int]
    total: int


class PaperAggregator:
    """Aggregates papers across sources with concurrent execution."""

    def __init__(self, clients: Optional[Dict[str, BaseSourceClient]] = None, max_workers: int = 3):
        self.clients = clients or _default_clients()
        self.max_workers = max(1, max_workers)

    def list_sources(self) -> List[str]:
        return sorted(self.clients.keys())

    def aggregate_papers_parallel(
        self,
        query: str,
        limit: int = 10,
        sources: Optional[List[str]] = None,
        enable_deduplication: bool = True,
    ) -> List[Paper]:
        query = (query or "").strip()
        if not query:
            return []

        source_names = sources or self.list_sources()
        invalid_sources = [name for name in source_names if name not in self.clients]
        if invalid_sources:
            raise ValueError(f"Invalid source(s): {', '.join(sorted(invalid_sources))}")

        limit = max(1, int(limit))
        papers: List[Paper] = []

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(source_names))) as executor:
            future_map = {
                executor.submit(self._fetch_from_source, source_name, query, limit): source_name
                for source_name in source_names
            }
            for future in as_completed(future_map):
                source_name = future_map[future]
                try:
                    result = future.result()
                    papers.extend(result)
                    logger.debug("Fetched %s papers from %s", len(result), source_name)
                except Exception as exc:
                    logger.warning("Source %s failed: %s", source_name, exc)

        if enable_deduplication:
            papers = deduplicate_papers(papers)

        return self._sort_papers(papers)

    def _fetch_from_source(self, source_name: str, query: str, limit: int) -> List[Paper]:
        client = self.clients[source_name]
        result = client.fetch_papers(query=query, limit=limit)
        return [paper for paper in result if isinstance(paper, Paper)]

    @staticmethod
    def _sort_papers(papers: Iterable[Paper]) -> List[Paper]:
        def key(paper: Paper) -> tuple:
            year = parse_year(paper.published_date) or 0
            citations = paper.citations or 0
            return (-year, -citations, paper.title.lower())

        return sorted(list(papers), key=key)


# Backward-compatible helper

def aggregate_papers(query: str, limit: int = 10, sources: Optional[List[str]] = None) -> List[Paper]:
    aggregator = PaperAggregator()
    return aggregator.aggregate_papers_parallel(query=query, limit=limit, sources=sources)
