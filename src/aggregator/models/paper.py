from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import re
from typing import Any, Dict, List, Optional


_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_URL_RE = re.compile(
    r"^https?://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\.?|"
    r"localhost|"
    r"\d{1,3}(?:\.\d{1,3}){3})"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


@dataclass(eq=False)
class Paper:
    """Canonical paper entity used across all source clients and storage layers."""

    title: str
    authors: List[str] = field(default_factory=list)
    published_date: Optional[str] = None
    source: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    citations: Optional[int] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    pdf_url: Optional[str] = None
    arxiv_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    semantic_scholar_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.title = (self.title or "").strip()
        if not self.title:
            raise ValueError("Paper title cannot be empty")

        self.authors = self._normalize_str_list(self.authors)
        self.keywords = self._normalize_str_list(self.keywords)

        self.abstract = self._normalize_optional_text(self.abstract)
        self.source = self._normalize_optional_text(self.source)
        self.published_date = self._normalize_optional_text(self.published_date)
        self.doi = self._normalize_optional_text(self.doi)
        self.journal = self._normalize_optional_text(self.journal)
        self.volume = self._normalize_optional_text(self.volume)
        self.issue = self._normalize_optional_text(self.issue)
        self.pages = self._normalize_optional_text(self.pages)
        self.arxiv_id = self._normalize_optional_text(self.arxiv_id)
        self.pubmed_id = self._normalize_optional_text(self.pubmed_id)
        self.semantic_scholar_id = self._normalize_optional_text(self.semantic_scholar_id)

        self.url = self._normalize_url(self.url)
        self.pdf_url = self._normalize_url(self.pdf_url)

        if self.citations is not None:
            try:
                self.citations = max(0, int(self.citations))
            except (TypeError, ValueError):
                self.citations = None

    @staticmethod
    def _normalize_str_list(items: Optional[List[str]]) -> List[str]:
        if not items:
            return []

        normalized: List[str] = []
        seen = set()
        for item in items:
            cleaned = (item or "").strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                normalized.append(cleaned)
        return normalized

    @staticmethod
    def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @classmethod
    def _normalize_url(cls, value: Optional[str]) -> Optional[str]:
        cleaned = cls._normalize_optional_text(value)
        if not cleaned:
            return None
        return cleaned if cls._is_valid_url(cleaned) else None

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        return bool(_URL_RE.match(url))

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if key == "created_at":
                payload[key] = value.isoformat() if value else None
            else:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paper":
        clean_data = dict(data)
        created_at = clean_data.get("created_at")
        if isinstance(created_at, str):
            try:
                clean_data["created_at"] = datetime.fromisoformat(created_at)
            except ValueError:
                clean_data.pop("created_at", None)

        valid_fields = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in clean_data.items() if k in valid_fields}
        return cls(**filtered)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "Paper":
        return cls.from_dict(json.loads(json_str))

    def get_primary_author(self) -> str:
        return self.authors[0] if self.authors else "Unknown"

    def get_author_list_str(self, max_authors: int = 3) -> str:
        if not self.authors:
            return "Unknown"

        if len(self.authors) <= max_authors:
            return ", ".join(self.authors)

        return f"{', '.join(self.authors[:max_authors])}, et al."

    def get_publication_year(self) -> str:
        if not self.published_date:
            return "Unknown"

        match = _YEAR_RE.search(str(self.published_date))
        return match.group(0) if match else "Unknown"

    def is_recent(self, years: int = 5) -> bool:
        if years < 0:
            return False

        try:
            year = int(self.get_publication_year())
        except ValueError:
            return False

        current_year = datetime.now(UTC).year
        return (current_year - year) <= years

    def has_pdf(self) -> bool:
        return bool(self.pdf_url)

    def get_formatted_citation(self) -> str:
        authors = self.get_author_list_str()
        year = self.get_publication_year()
        parts = [f"{authors} ({year}). {self.title}."]

        if self.journal:
            journal = self.journal
            if self.volume:
                journal += f", {self.volume}"
                if self.issue:
                    journal += f"({self.issue})"
            if self.pages:
                journal += f", {self.pages}"
            parts.append(journal)

        if self.doi:
            parts.append(f"DOI: {self.doi}")

        return " ".join(parts)

    def __str__(self) -> str:
        return f"{self.title} - {self.get_author_list_str()} ({self.get_publication_year()})"

    def __repr__(self) -> str:
        return (
            f"Paper(title={self.title!r}, source={self.source!r}, "
            f"authors={len(self.authors)}, year={self.get_publication_year()!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Paper):
            return False

        return (
            self.title.lower() == other.title.lower()
            and self.get_primary_author().lower() == other.get_primary_author().lower()
        )

    def __hash__(self) -> int:
        key = (self.title.lower(), self.get_primary_author().lower())
        return hash(key)
