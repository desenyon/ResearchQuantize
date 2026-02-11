from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    default_query_limit: int = 10
    default_source: str = "arxiv"
    default_year_filter: int | None = None
    arxiv_api_key: str = ""
    pubmed_api_key: str = ""
    semantic_scholar_api_key: str = ""
    database_path: str = "papers.db"

    @classmethod
    def from_env(cls) -> "Settings":
        default_limit_raw = os.getenv("DEFAULT_QUERY_LIMIT", "10")
        try:
            default_limit = max(1, int(default_limit_raw))
        except ValueError:
            default_limit = 10

        return cls(
            default_query_limit=default_limit,
            default_source=os.getenv("DEFAULT_SOURCE", "arxiv"),
            default_year_filter=_parse_optional_int(os.getenv("DEFAULT_YEAR_FILTER")),
            arxiv_api_key=os.getenv("ARXIV_API_KEY", ""),
            pubmed_api_key=os.getenv("PUBMED_API_KEY", ""),
            semantic_scholar_api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY", ""),
            database_path=os.getenv("DATABASE_PATH", "papers.db"),
        )


def _parse_optional_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


settings = Settings.from_env()

DEFAULT_QUERY_LIMIT = settings.default_query_limit
DEFAULT_SOURCE = settings.default_source
DEFAULT_YEAR_FILTER = settings.default_year_filter
ARXIV_API_KEY = settings.arxiv_api_key
PUBMED_API_KEY = settings.pubmed_api_key
SEMANTIC_SCHOLAR_API_KEY = settings.semantic_scholar_api_key
DATABASE_PATH = settings.database_path
