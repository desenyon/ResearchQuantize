import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from aggregator.core import PaperAggregator, aggregate_papers
from aggregator.models.paper import Paper


class FakeClient:
    def __init__(self, papers):
        self._papers = papers

    def fetch_papers(self, query, limit=10):
        return self._papers[:limit]


class TestCore(unittest.TestCase):
    def setUp(self):
        self.arxiv_papers = [
            Paper(
                title="Neural Search at Scale",
                authors=["Alice"],
                published_date="2024-01-10",
                source="arxiv",
                citations=10,
            ),
            Paper(
                title="Graph Transformers",
                authors=["Bob"],
                published_date="2023-06-11",
                source="arxiv",
            ),
        ]
        self.semantic_papers = [
            Paper(
                title="Neural Search at Scale",
                authors=["Alice"],
                published_date="2024-01-10",
                source="semantic_scholar",
                abstract="Better abstract content",
                doi="10.1000/test",
            )
        ]

    def test_paper_model_basics(self):
        paper = Paper(title="Test", authors=["A", "B"], published_date="2022-01-01")
        self.assertEqual(paper.get_primary_author(), "A")
        self.assertEqual(paper.get_publication_year(), "2022")
        self.assertIn("Test", paper.get_formatted_citation())

    def test_aggregate_with_deduplication(self):
        aggregator = PaperAggregator(
            clients={
                "arxiv": FakeClient(self.arxiv_papers),
                "semantic_scholar": FakeClient(self.semantic_papers),
            },
            max_workers=2,
        )

        papers = aggregator.aggregate_papers_parallel("neural search", limit=5)
        titles = [paper.title for paper in papers]

        self.assertEqual(len(papers), 2)
        self.assertIn("Neural Search at Scale", titles)
        self.assertIn("Graph Transformers", titles)

    def test_aggregate_specific_source(self):
        aggregator = PaperAggregator(clients={"arxiv": FakeClient(self.arxiv_papers)})
        papers = aggregator.aggregate_papers_parallel("query", limit=10, sources=["arxiv"])
        self.assertTrue(all(p.source == "arxiv" for p in papers))

    def test_invalid_source_raises(self):
        aggregator = PaperAggregator(clients={"arxiv": FakeClient(self.arxiv_papers)})
        with self.assertRaises(ValueError):
            aggregator.aggregate_papers_parallel("query", sources=["invalid"])

    def test_legacy_aggregate_function(self):
        papers = aggregate_papers("machine learning", limit=1, sources=["arxiv"])
        self.assertIsInstance(papers, list)


if __name__ == "__main__":
    unittest.main()
