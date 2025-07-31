# src/aggregator/sources/__init__.py

from .arxiv import ArxivClient
from .pubmed import PubmedClient
from .semantic_scholar import SemanticScholarClient

__all__ = ['ArxivClient', 'PubmedClient', 'SemanticScholarClient']