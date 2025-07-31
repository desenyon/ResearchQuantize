# src/tests/test_core.py

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aggregator.core import aggregate_papers, PaperAggregator
from aggregator.models.paper import Paper

class TestCore(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = PaperAggregator()
        self.test_query = "machine learning"
        self.test_limit = 3
    
    def test_paper_model(self):
        """Test Paper model functionality."""
        paper = Paper(
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            published_date="2023-01-01",
            source="Test Source"
        )
        
        self.assertEqual(paper.title, "Test Paper")
        self.assertEqual(len(paper.authors), 2)
        self.assertEqual(paper.get_primary_author(), "Author 1")
        self.assertEqual(paper.get_publication_year(), "2023")
        self.assertTrue(paper.is_recent(years=5))
    
    def test_paper_to_dict(self):
        """Test Paper serialization."""
        paper = Paper(
            title="Test Paper",
            authors=["Author 1"],
            published_date="2023-01-01",
            source="Test"
        )
        
        paper_dict = paper.to_dict()
        self.assertIsInstance(paper_dict, dict)
        self.assertEqual(paper_dict['title'], "Test Paper")
        
        # Test round-trip conversion
        paper2 = Paper.from_dict(paper_dict)
        self.assertEqual(paper.title, paper2.title)
        self.assertEqual(paper.authors, paper2.authors)
    
    def test_aggregate_papers_legacy(self):
        """Test legacy aggregate_papers function."""
        papers = aggregate_papers(self.test_query, limit=self.test_limit)
        self.assertIsInstance(papers, list)
        # Note: May be empty if no internet or API issues
        for paper in papers:
            self.assertIsInstance(paper, Paper)
            self.assertIsNotNone(paper.title)
    
    def test_paper_aggregator_init(self):
        """Test PaperAggregator initialization."""
        self.assertIsNotNone(self.aggregator.clients)
        self.assertEqual(len(self.aggregator.clients), 3)  # 3 sources (removed Google Scholar)
    
    def test_paper_aggregator_sources(self):
        """Test aggregation with specific sources."""
        sources = ['arxiv']
        papers = self.aggregator.aggregate_papers_parallel(
            self.test_query, 
            limit=2, 
            sources=sources
        )
        
        self.assertIsInstance(papers, list)
        # Check that papers are from specified source if any returned
        for paper in papers:
            if paper.source:
                self.assertIn(paper.source.lower(), ['arxiv'])
    
    def test_deduplication_disabled(self):
        """Test aggregation with deduplication disabled."""
        papers = self.aggregator.aggregate_papers_parallel(
            self.test_query,
            limit=2,
            enable_deduplication=False
        )
        
        self.assertIsInstance(papers, list)

if __name__ == "__main__":
    unittest.main()