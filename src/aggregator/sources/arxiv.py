from __future__ import annotations

import re
import time
from typing import List, Optional
from xml.etree import ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseSourceClient
from ..models.paper import Paper
from ..utils.helpers import clean_string
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ArxivClient(BaseSourceClient):
    """ArXiv API client with retry, timeout, and parser-level safety."""

    source_name = "arxiv"
    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self, session: Optional[requests.Session] = None, rate_limit_delay: float = 3.0):
        self.session = session or requests.Session()
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0
        self._setup_session()

    def _setup_session(self) -> None:
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({
            "User-Agent": "ResearchQuantize/2.0 (+https://github.com/desenyon/ResearchQuantize)"
        })

    def _rate_limit(self) -> None:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def fetch_papers(self, query: str, limit: int = 10) -> List[Paper]:
        query = clean_string(query)
        if not query:
            return []

        params = {
            "search_query": self._build_search_query(query),
            "start": 0,
            "max_results": max(1, min(limit, 200)),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            self._rate_limit()
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            return self._parse_response(response.text)
        except requests.RequestException as exc:
            logger.warning("ArXiv request failed: %s", exc)
            return []

    def _build_search_query(self, query: str) -> str:
        lowered = query.lower()
        if any(prefix in lowered for prefix in ["ti:", "au:", "abs:", "cat:", "all:"]):
            return query
        return f'ti:"{query}" OR abs:"{query}"'

    def _parse_response(self, xml_data: str) -> List[Paper]:
        if not xml_data.strip():
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as exc:
            logger.warning("Failed to parse ArXiv response XML: %s", exc)
            return []

        papers: List[Paper] = []
        for entry in root.findall("atom:entry", ns):
            paper = self._parse_entry(entry, ns)
            if paper:
                papers.append(paper)

        return papers

    def _parse_entry(self, entry: ET.Element, ns: dict) -> Optional[Paper]:
        title = clean_string(self._entry_text(entry, "atom:title", ns))
        if not title:
            return None

        authors = [
            clean_string(author.text)
            for author in entry.findall("atom:author/atom:name", ns)
            if author.text
        ]

        abstract = clean_string(self._entry_text(entry, "atom:summary", ns))
        published = clean_string(self._entry_text(entry, "atom:published", ns))
        url = clean_string(self._entry_text(entry, "atom:id", ns))
        doi = clean_string(self._entry_text(entry, "arxiv:doi", ns)) or None

        categories = [
            clean_string(category.attrib.get("term", ""))
            for category in entry.findall("atom:category", ns)
            if category.attrib.get("term")
        ]

        pdf_url = None
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href")
                break

        arxiv_id = None
        match = re.search(r"arxiv\.org/abs/([^/?#]+)", url)
        if match:
            arxiv_id = match.group(1)

        try:
            return Paper(
                title=title,
                authors=authors,
                published_date=published,
                source="arxiv",
                abstract=abstract,
                url=url,
                doi=doi,
                keywords=categories,
                pdf_url=pdf_url,
                arxiv_id=arxiv_id,
            )
        except ValueError:
            return None

    @staticmethod
    def _entry_text(entry: ET.Element, path: str, ns: dict) -> str:
        node = entry.find(path, ns)
        return node.text if node is not None and node.text else ""

    def search_by_category(self, category: str, limit: int = 10) -> List[Paper]:
        return self.fetch_papers(f"cat:{category}", limit=limit)

    def search_by_author(self, author: str, limit: int = 10) -> List[Paper]:
        return self.fetch_papers(f'au:"{clean_string(author)}"', limit=limit)
