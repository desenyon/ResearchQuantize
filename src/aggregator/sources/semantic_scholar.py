from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseSourceClient
from ..models.paper import Paper
from ..utils.helpers import clean_string
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SemanticScholarClient(BaseSourceClient):
    """Semantic Scholar Graph API client with resilient parsing."""

    source_name = "semantic_scholar"
    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        rate_limit_delay: float = 0.1,
    ):
        self.api_key = api_key
        self.session = session or requests.Session()
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0
        self._setup_session()

    def _setup_session(self) -> None:
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        headers = {"User-Agent": "ResearchQuantize/2.0 (+https://github.com/desenyon/ResearchQuantize)"}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        self.session.headers.update(headers)

    def _rate_limit(self) -> None:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def fetch_papers(self, query: str, limit: int = 10) -> List[Paper]:
        query = clean_string(query)
        if not query:
            return []

        fields = [
            "title",
            "authors",
            "year",
            "publicationDate",
            "abstract",
            "url",
            "venue",
            "citationCount",
            "fieldsOfStudy",
            "externalIds",
            "openAccessPdf",
        ]
        params = {"query": query, "limit": max(1, min(limit, 100)), "fields": ",".join(fields)}

        try:
            self._rate_limit()
            response = self.session.get(f"{self.BASE_URL}/paper/search", params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            return self._parse_response(payload)
        except requests.RequestException as exc:
            logger.warning("Semantic Scholar request failed: %s", exc)
            return []

    def _parse_response(self, payload: Dict[str, Any]) -> List[Paper]:
        data = payload.get("data", [])
        papers: List[Paper] = []
        for paper_data in data:
            paper = self._parse_paper_data(paper_data)
            if paper:
                papers.append(paper)
        return papers

    def _parse_paper_data(self, paper_data: Dict[str, Any]) -> Optional[Paper]:
        title = clean_string(paper_data.get("title"))
        if not title:
            return None

        authors = [
            clean_string(author.get("name"))
            for author in paper_data.get("authors", [])
            if isinstance(author, dict) and author.get("name")
        ]

        publication_date = paper_data.get("publicationDate")
        year = paper_data.get("year")
        published_date = str(publication_date or year or "").strip() or None

        external_ids = paper_data.get("externalIds", {}) or {}
        fields_of_study = [clean_string(x) for x in paper_data.get("fieldsOfStudy", []) if x]
        open_access_pdf = paper_data.get("openAccessPdf") or {}

        try:
            return Paper(
                title=title,
                authors=authors,
                published_date=published_date,
                source="semantic_scholar",
                abstract=clean_string(paper_data.get("abstract")) or None,
                url=clean_string(paper_data.get("url")) or None,
                doi=clean_string(external_ids.get("DOI")) or None,
                keywords=fields_of_study,
                citations=paper_data.get("citationCount"),
                journal=clean_string(paper_data.get("venue")) or None,
                pdf_url=clean_string(open_access_pdf.get("url")) or None,
                arxiv_id=clean_string(external_ids.get("ArXiv")) or None,
                pubmed_id=clean_string(external_ids.get("PubMed")) or None,
                semantic_scholar_id=clean_string(paper_data.get("paperId")) or None,
            )
        except ValueError:
            return None

    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        paper_id = clean_string(paper_id)
        if not paper_id:
            return None

        fields = [
            "title",
            "authors",
            "year",
            "publicationDate",
            "abstract",
            "url",
            "venue",
            "citationCount",
            "fieldsOfStudy",
            "externalIds",
            "openAccessPdf",
        ]

        try:
            self._rate_limit()
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}", params={"fields": ",".join(fields)}, timeout=30
            )
            response.raise_for_status()
            return self._parse_paper_data(response.json())
        except requests.RequestException as exc:
            logger.warning("Semantic Scholar fetch by id failed: %s", exc)
            return None

    def search_by_author(self, author: str, limit: int = 10) -> List[Paper]:
        return self.fetch_papers(f'author:"{clean_string(author)}"', limit=limit)
