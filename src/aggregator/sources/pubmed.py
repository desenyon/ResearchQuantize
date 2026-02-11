from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseSourceClient
from ..models.paper import Paper
from ..utils.helpers import clean_string
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PubmedClient(BaseSourceClient):
    """PubMed Entrez client using `esearch` + `esummary` JSON endpoints."""

    source_name = "pubmed"
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def __init__(self, session: Optional[requests.Session] = None, email: str = "paperengine@example.com"):
        self.session = session or requests.Session()
        self.email = email
        self._setup_session()

    def _setup_session(self) -> None:
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update(
            {"User-Agent": "ResearchQuantize/2.0 (+https://github.com/desenyon/ResearchQuantize)"}
        )

    def fetch_papers(self, query: str, limit: int = 10) -> List[Paper]:
        query = clean_string(query)
        if not query:
            return []

        try:
            ids = self._search_ids(query, limit=max(1, min(limit, 100)))
            if not ids:
                return []

            summary_data = self._fetch_summaries(ids)
            return self._parse_summary_data(summary_data)
        except requests.RequestException as exc:
            logger.warning("PubMed request failed: %s", exc)
            return []

    def _search_ids(self, query: str, limit: int) -> List[str]:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": limit,
            "retmode": "json",
            "tool": "ResearchQuantize",
            "email": self.email,
        }
        response = self.session.get(self.ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return payload.get("esearchresult", {}).get("idlist", [])

    def _fetch_summaries(self, ids: List[str]) -> Dict[str, Any]:
        params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
            "tool": "ResearchQuantize",
            "email": self.email,
        }
        response = self.session.get(self.ESUMMARY_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def _parse_summary_data(self, payload: Dict[str, Any]) -> List[Paper]:
        result = payload.get("result", {})
        uids = result.get("uids", [])
        papers: List[Paper] = []

        for uid in uids:
            record = result.get(uid, {})
            title = clean_string(record.get("title"))
            if not title:
                continue

            authors = [clean_string(author.get("name")) for author in record.get("authors", []) if author.get("name")]
            published_date = clean_string(record.get("pubdate")) or None
            journal = clean_string(record.get("fulljournalname")) or None
            doi = self._extract_doi(record.get("articleids", []))
            url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"

            try:
                papers.append(
                    Paper(
                        title=title,
                        authors=authors,
                        published_date=published_date,
                        source="pubmed",
                        journal=journal,
                        doi=doi,
                        url=url,
                        pubmed_id=str(uid),
                    )
                )
            except ValueError:
                continue

        return papers

    @staticmethod
    def _extract_doi(article_ids: List[Dict[str, str]]) -> Optional[str]:
        for item in article_ids:
            if item.get("idtype") == "doi":
                return clean_string(item.get("value")) or None
        return None
