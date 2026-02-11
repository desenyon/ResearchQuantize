import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from aggregator.core import PaperAggregator
from aggregator.models.paper import Paper
from aggregator.search.engine import search_papers
from aggregator.search.filters import filter_by_author, filter_by_year


class FakeClient:
    def __init__(self, papers):
        self._papers = papers

    def fetch_papers(self, query, limit=10):
        return self._papers[:limit]


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.papers = [
            Paper(title="Paper 2023", authors=["Alice"], published_date="2023-05-01", source="arxiv"),
            Paper(title="Paper 2024", authors=["Bob"], published_date="2024-06-15", source="arxiv"),
            Paper(
                title="Semantic Paper",
                authors=["Carol"],
                published_date="2024-01-01",
                source="semantic_scholar",
            ),
        ]

        self.aggregator = PaperAggregator(
            clients={
                "arxiv": FakeClient(self.papers[:2]),
                "semantic_scholar": FakeClient(self.papers[2:]),
            }
        )

    def test_search_all_sources(self):
        results = search_papers("query", aggregator=self.aggregator, limit=10)
        self.assertEqual(len(results), 3)

    def test_search_with_source_filter(self):
        results = search_papers("query", source="arxiv", aggregator=self.aggregator, limit=10)
        self.assertTrue(all(p.source == "arxiv" for p in results))

    def test_search_with_year_filter(self):
        results = search_papers("query", year=2024, aggregator=self.aggregator, limit=10)
        self.assertEqual({p.get_publication_year() for p in results}, {"2024"})

    def test_invalid_source(self):
        with self.assertRaises(ValueError):
            search_papers("query", source="invalid", aggregator=self.aggregator)

    def test_filter_helpers(self):
        by_author = filter_by_author(self.papers, "alice")
        by_year = filter_by_year(self.papers, 2024)
        self.assertEqual(len(by_author), 1)
        self.assertEqual(len(by_year), 2)


if __name__ == "__main__":
    unittest.main()
