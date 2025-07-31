# src/tests/test_search.py

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aggregator.search.engine import search_papers
from aggregator.models.paper import Paper

class TestSearch(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.test_query = "machine learning"
    
    def test_search_papers(self):
        """Test basic paper search functionality."""
        papers = search_papers(self.test_query)
        self.assertIsInstance(papers, list)
        
        # Verify paper structure if any papers returned
        for paper in papers:
            self.assertIsInstance(paper, Paper)
            self.assertIsNotNone(paper.title)
    
    def test_search_with_source_filter(self):
        """Test search with source filtering."""
        papers = search_papers(self.test_query, source="arxiv")
        self.assertIsInstance(papers, list)
        
        # Check source filtering if papers returned
        for paper in papers:
            if paper.source:
                self.assertIn(paper.source.lower(), ['arxiv'])
    
    def test_search_with_year_filter(self):
        """Test search with year filtering."""
        papers = search_papers(self.test_query, year=2023)
        self.assertIsInstance(papers, list)
        
        # Check year filtering if papers returned
        for paper in papers:
            if paper.published_date:
                year = paper.get_publication_year()
                if year.isdigit():
                    # Should be close to 2023 (API might return range)
                    self.assertTrue(2020 <= int(year) <= 2025)
    
    def test_search_invalid_source(self):
        """Test search with invalid source."""
        with self.assertRaises(ValueError):
            search_papers(self.test_query, source="invalid_source")

if __name__ == "__main__":
    unittest.main()