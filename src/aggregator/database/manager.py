from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from ..models.paper import Paper
from ..utils.logger import setup_logger
from .schema import SCHEMA_SQL

logger = setup_logger(__name__)


class DatabaseManager:
    """SQLite storage for papers with idempotent inserts."""

    def __init__(self, db_path: str = "papers.db"):
        self.db_path = str(Path(db_path))
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._initialize_db()

    def _connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _initialize_db(self) -> None:
        assert self.conn is not None
        self.conn.execute(SCHEMA_SQL)
        self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def save_paper(self, paper: Paper) -> None:
        self.save_papers([paper])

    def save_papers(self, papers: Iterable[Paper]) -> int:
        assert self.conn is not None
        rows = [self._paper_to_row(paper) for paper in papers]
        if not rows:
            return 0

        before = self.conn.total_changes
        with self.conn:
            self.conn.executemany(
                """
                INSERT OR IGNORE INTO papers (
                    title, authors_json, published_date, source, abstract, url, doi,
                    keywords_json, citations, journal, volume, issue, pages, pdf_url,
                    arxiv_id, pubmed_id, semantic_scholar_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

        return self.conn.total_changes - before

    def get_all_papers(self) -> List[Paper]:
        return self._fetch_papers("SELECT * FROM papers ORDER BY created_at DESC")

    def get_papers_by_source(self, source: str) -> List[Paper]:
        return self._fetch_papers(
            "SELECT * FROM papers WHERE source = ? ORDER BY created_at DESC", params=(source,)
        )

    def count_papers(self) -> int:
        assert self.conn is not None
        row = self.conn.execute("SELECT COUNT(*) AS n FROM papers").fetchone()
        return int(row["n"]) if row else 0

    def paper_exists(self, title: str, authors: List[str]) -> bool:
        assert self.conn is not None
        authors_json = json.dumps(authors or [], ensure_ascii=False)
        row = self.conn.execute(
            "SELECT 1 FROM papers WHERE title = ? AND authors_json = ? LIMIT 1",
            (title, authors_json),
        ).fetchone()
        return row is not None

    def _fetch_papers(self, query: str, params: tuple = ()) -> List[Paper]:
        assert self.conn is not None
        rows = self.conn.execute(query, params).fetchall()
        papers: List[Paper] = []

        for row in rows:
            try:
                papers.append(
                    Paper.from_dict(
                        {
                            "title": row["title"],
                            "authors": json.loads(row["authors_json"]),
                            "published_date": row["published_date"],
                            "source": row["source"],
                            "abstract": row["abstract"],
                            "url": row["url"],
                            "doi": row["doi"],
                            "keywords": json.loads(row["keywords_json"]),
                            "citations": row["citations"],
                            "journal": row["journal"],
                            "volume": row["volume"],
                            "issue": row["issue"],
                            "pages": row["pages"],
                            "pdf_url": row["pdf_url"],
                            "arxiv_id": row["arxiv_id"],
                            "pubmed_id": row["pubmed_id"],
                            "semantic_scholar_id": row["semantic_scholar_id"],
                            "created_at": row["created_at"],
                        }
                    )
                )
            except Exception as exc:
                logger.warning("Skipping invalid DB row: %s", exc)

        return papers

    @staticmethod
    def _paper_to_row(paper: Paper) -> tuple:
        payload = paper.to_dict()
        return (
            payload["title"],
            json.dumps(payload.get("authors") or [], ensure_ascii=False),
            payload.get("published_date"),
            payload.get("source"),
            payload.get("abstract"),
            payload.get("url"),
            payload.get("doi"),
            json.dumps(payload.get("keywords") or [], ensure_ascii=False),
            payload.get("citations"),
            payload.get("journal"),
            payload.get("volume"),
            payload.get("issue"),
            payload.get("pages"),
            payload.get("pdf_url"),
            payload.get("arxiv_id"),
            payload.get("pubmed_id"),
            payload.get("semantic_scholar_id"),
            payload.get("created_at"),
        )
