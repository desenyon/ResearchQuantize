from __future__ import annotations

from typing import List

from ..models.paper import Paper
from ..utils.helpers import parse_year


def filter_by_author(papers: List[Paper], author_name: str) -> List[Paper]:
    needle = (author_name or "").strip().lower()
    if not needle:
        return list(papers)

    return [
        paper
        for paper in papers
        if any(needle in (author or "").lower() for author in (paper.authors or []))
    ]


def filter_by_year(papers: List[Paper], year: int) -> List[Paper]:
    return [paper for paper in papers if parse_year(paper.published_date) == year]
