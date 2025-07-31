# src/tests/test_sources.py

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aggregator.sources.arxiv import ArxivClient
from aggregator.sources.semantic_scholar import SemanticScholarClient
from aggregator.models.paper import Paper

class TestSources(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.arxiv_client = ArxivClient()
        self.semantic_client = SemanticScholarClient()
        self.test_query = "quantum computing"
        self.test_limit = 3
    
    def test_arxiv_client_init(self):
        """Test ArXiv client initialization."""
        self.assertIsNotNone(self.arxiv_client.session)
        self.assertEqual(self.arxiv_client.rate_limit_delay, 3)
    
    def test_arxiv_fetch_papers(self):
        """Test ArXiv paper fetching."""
        papers = self.arxiv_client.fetch_papers(self.test_query, limit=self.test_limit)
        self.assertIsInstance(papers, list)
        
        # Verify paper structure
        for paper in papers:
            self.assertIsInstance(paper, Paper)
            self.assertIsNotNone(paper.title)
            self.assertEqual(paper.source, "ArXiv")
    
    def test_arxiv_search_by_category(self):
        """Test ArXiv category search."""
        papers = self.arxiv_client.search_by_category("cs.AI", limit=2)
        self.assertIsInstance(papers, list)
        
        for paper in papers:
            self.assertIsInstance(paper, Paper)
            self.assertEqual(paper.source, "ArXiv")
    
    def test_semantic_scholar_client_init(self):
        """Test Semantic Scholar client initialization."""
        self.assertIsNotNone(self.semantic_client.session)
        self.assertEqual(self.semantic_client.rate_limit_delay, 0.1)
    
    def test_semantic_scholar_fetch_papers(self):
        """Test Semantic Scholar paper fetching."""
        papers = self.semantic_client.fetch_papers(self.test_query, limit=self.test_limit)
        self.assertIsInstance(papers, list)
        
        # Verify paper structure
        for paper in papers:
            self.assertIsInstance(paper, Paper)
            self.assertIsNotNone(paper.title)
            self.assertEqual(paper.source, "Semantic Scholar")
    
    def test_paper_validation(self):
        """Test paper data validation."""
        # Test valid paper
        valid_paper = Paper(
            title="Valid Paper Title",
            authors=["Author 1", "Author 2"],
            published_date="2023-01-01",
            source="Test"
        )
        self.assertEqual(valid_paper.title, "Valid Paper Title")
        
        # Test paper with invalid URL (should be set to None)
        paper_with_invalid_url = Paper(
            title="Test Paper",
            authors=["Author"],
            published_date="2023",
            source="Test",
            url="invalid-url"
        )
        self.assertIsNone(paper_with_invalid_url.url)
    
    def test_paper_methods(self):
        """Test paper utility methods."""
        paper = Paper(
            title="A Very Long Paper Title That Should Be Truncated",
            authors=["First Author", "Second Author", "Third Author", "Fourth Author"],
            published_date="2023-06-15",
            source="Test",
            citations=42
        )
        
        # Test author methods
        self.assertEqual(paper.get_primary_author(), "First Author")
        author_str = paper.get_author_list_str(max_authors=2)
        self.assertIn("et al.", author_str)
        
        # Test year extraction
        self.assertEqual(paper.get_publication_year(), "2023")
        
        # Test recent check
        self.assertTrue(paper.is_recent(years=2))
        self.assertFalse(paper.is_recent(years=0))
        
        # Test citation formatting
        citation = paper.get_formatted_citation()
        self.assertIn(paper.title, citation)
        self.assertIn("2023", citation)

if __name__ == "__main__":
    unittest.main()
