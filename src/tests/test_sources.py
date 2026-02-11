import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from aggregator.models.paper import Paper
from aggregator.sources.arxiv import ArxivClient
from aggregator.sources.pubmed import PubmedClient
from aggregator.sources.semantic_scholar import SemanticScholarClient


ARXIV_XML = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<feed xmlns=\"http://www.w3.org/2005/Atom\" xmlns:arxiv=\"http://arxiv.org/schemas/atom\">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <updated>2024-01-10T00:00:00Z</updated>
    <published>2024-01-09T00:00:00Z</published>
    <title> Test Driven Research </title>
    <summary>  A robust approach. </summary>
    <author><name>Alice</name></author>
    <author><name>Bob</name></author>
    <arxiv:doi>10.1000/arxiv.test</arxiv:doi>
    <link href=\"http://arxiv.org/abs/2401.12345v1\" rel=\"alternate\" type=\"text/html\"/>
    <link href=\"http://arxiv.org/pdf/2401.12345v1\" rel=\"related\" type=\"application/pdf\"/>
    <category term=\"cs.AI\"/>
  </entry>
</feed>
"""


class TestSources(unittest.TestCase):
    def test_arxiv_parse_response(self):
        client = ArxivClient(rate_limit_delay=0)
        papers = client._parse_response(ARXIV_XML)

        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertIsInstance(paper, Paper)
        self.assertEqual(paper.title, "Test Driven Research")
        self.assertEqual(paper.source, "arxiv")
        self.assertEqual(paper.arxiv_id, "2401.12345v1")
        self.assertIn("cs.AI", paper.keywords)

    def test_pubmed_summary_parse(self):
        client = PubmedClient()
        payload = {
            "result": {
                "uids": ["12345"],
                "12345": {
                    "title": "Clinical Study",
                    "pubdate": "2023 Jan",
                    "fulljournalname": "Medical Journal",
                    "authors": [{"name": "Dr A"}],
                    "articleids": [{"idtype": "doi", "value": "10.1/test"}],
                },
            }
        }

        papers = client._parse_summary_data(payload)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].source, "pubmed")
        self.assertEqual(papers[0].doi, "10.1/test")

    def test_semantic_scholar_parse(self):
        client = SemanticScholarClient(rate_limit_delay=0)
        payload = {
            "title": "Semantic Results",
            "authors": [{"name": "Alice"}],
            "year": 2024,
            "abstract": "summary",
            "venue": "ICML",
            "citationCount": 42,
            "fieldsOfStudy": ["Computer Science"],
            "externalIds": {"DOI": "10.2/abc", "ArXiv": "2401.00001"},
            "openAccessPdf": {"url": "https://example.com/paper.pdf"},
            "paperId": "abcdef",
        }

        paper = client._parse_paper_data(payload)
        self.assertIsNotNone(paper)
        assert paper is not None
        self.assertEqual(paper.source, "semantic_scholar")
        self.assertEqual(paper.citations, 42)
        self.assertEqual(paper.semantic_scholar_id, "abcdef")

    def test_source_network_failures_return_empty(self):
        response_error = requests.RequestException("boom")

        arxiv = ArxivClient(rate_limit_delay=0)
        arxiv.session.get = MagicMock(side_effect=response_error)
        self.assertEqual(arxiv.fetch_papers("query"), [])

        pubmed = PubmedClient()
        pubmed.session.get = MagicMock(side_effect=response_error)
        self.assertEqual(pubmed.fetch_papers("query"), [])

        semantic = SemanticScholarClient(rate_limit_delay=0)
        semantic.session.get = MagicMock(side_effect=response_error)
        self.assertEqual(semantic.fetch_papers("query"), [])


if __name__ == "__main__":
    unittest.main()
