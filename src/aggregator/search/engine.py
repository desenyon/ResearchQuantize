from __future__ import annotations

from typing import List, Optional

from ..core import PaperAggregator
from ..models.paper import Paper
from ..utils.helpers import filter_papers_by_year
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def search_papers(
    query: str,
    source: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 10,
    aggregator: Optional[PaperAggregator] = None,
) -> List[Paper]:
    """Search papers across one or many sources with optional filtering."""
    engine = aggregator or PaperAggregator()

    if source and source not in engine.clients:
        raise ValueError(f"Invalid source: {source}")

    sources = [source] if source else None
    papers = engine.aggregate_papers_parallel(query=query, limit=limit, sources=sources)

    if year is not None:
        papers = filter_papers_by_year(papers, year)

    logger.info("Search returned %s papers", len(papers))
    return papers
