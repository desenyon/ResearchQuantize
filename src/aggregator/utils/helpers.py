from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher
import re
from typing import Any, Dict, Iterable, List, Optional

from ..models.paper import Paper
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def format_date(date_str: Optional[str]) -> str:
    """Convert common API date formats into a human-readable value."""
    if not date_str:
        return "Unknown"

    normalized = str(date_str).strip()
    if not normalized:
        return "Unknown"

    candidates = [
        ("%Y-%m-%d", normalized[:10]),
        ("%Y-%m", normalized[:7]),
        ("%Y", normalized[:4]),
        ("%Y-%m-%dT%H:%M:%SZ", normalized[:20]),
    ]

    for fmt, value in candidates:
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt == "%Y":
                return str(parsed.year)
            if fmt == "%Y-%m":
                return parsed.strftime("%B %Y")
            return parsed.strftime("%B %d, %Y")
        except ValueError:
            continue

    return normalized


def clean_string(text: Optional[str]) -> str:
    if not text:
        return ""

    cleaned = re.sub(r"<[^>]+>", "", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)
    return cleaned


def similarity_score(str1: str, str2: str) -> float:
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def normalize_title(title: Optional[str]) -> str:
    if not title:
        return ""

    normalized = re.sub(r"[^\w\s]", "", title.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _paper_quality_score(paper: Paper) -> int:
    score = 0
    score += 2 if paper.abstract else 0
    score += 1 if paper.doi else 0
    score += 1 if paper.url else 0
    score += 1 if paper.pdf_url else 0
    score += 1 if paper.citations is not None else 0
    score += min(len(paper.authors), 3)
    return score


def deduplicate_papers(papers: List[Paper], similarity_threshold: float = 0.96) -> List[Paper]:
    """De-duplicate by normalized title while preserving best metadata."""
    if not papers:
        return []

    groups: List[List[Paper]] = []
    group_titles: List[str] = []

    for paper in papers:
        normalized = normalize_title(paper.title)
        if not normalized:
            continue

        placed = False
        for idx, seen in enumerate(group_titles):
            if similarity_score(normalized, seen) >= similarity_threshold:
                groups[idx].append(paper)
                placed = True
                break

        if not placed:
            group_titles.append(normalized)
            groups.append([paper])

    deduped: List[Paper] = [max(group, key=_paper_quality_score) for group in groups]
    logger.info("Deduplicated %s papers down to %s", len(papers), len(deduped))
    return deduped


def merge_papers_by_similarity(papers: List[Paper], similarity_threshold: float = 0.95) -> List[Paper]:
    if not papers:
        return []

    merged: List[Paper] = []
    used = set()

    for i, base in enumerate(papers):
        if i in used:
            continue

        cluster = [base]
        base_norm = normalize_title(base.title)
        for j, candidate in enumerate(papers[i + 1 :], i + 1):
            if j in used:
                continue
            if similarity_score(base_norm, normalize_title(candidate.title)) >= similarity_threshold:
                cluster.append(candidate)
                used.add(j)

        merged.append(_merge_cluster(cluster))
        used.add(i)

    return merged


def _merge_cluster(papers: List[Paper]) -> Paper:
    if not papers:
        raise ValueError("Cannot merge empty paper cluster")
    if len(papers) == 1:
        return papers[0]

    best = max(papers, key=_paper_quality_score)

    all_authors = []
    seen = set()
    for paper in papers:
        for author in paper.authors:
            key = author.lower()
            if key not in seen:
                seen.add(key)
                all_authors.append(author)

    combined_sources = sorted({paper.source for paper in papers if paper.source})
    keywords = sorted({kw for paper in papers for kw in paper.keywords if kw})

    return Paper(
        title=max(papers, key=lambda p: len(p.title)).title,
        authors=all_authors,
        published_date=max((p.published_date for p in papers if p.published_date), default=best.published_date),
        source=", ".join(combined_sources) if combined_sources else best.source,
        abstract=best.abstract,
        url=best.url,
        doi=best.doi,
        keywords=keywords,
        citations=max((p.citations for p in papers if p.citations is not None), default=best.citations),
        journal=best.journal,
        volume=best.volume,
        issue=best.issue,
        pages=best.pages,
        pdf_url=best.pdf_url,
        arxiv_id=best.arxiv_id,
        pubmed_id=best.pubmed_id,
        semantic_scholar_id=best.semantic_scholar_id,
    )


def validate_paper_data(paper_data: Dict[str, Any]) -> bool:
    title = paper_data.get("title")
    return bool(title and str(title).strip())


def extract_keywords_from_title(title: str) -> List[str]:
    if not title:
        return []

    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "in",
        "is",
        "it",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
        "using",
        "based",
        "new",
        "novel",
    }

    words = re.findall(r"\b[a-zA-Z]{3,}\b", title.lower())
    keywords = [word for word in words if word not in stop_words]
    return keywords[:10]


def parse_year(value: Optional[str]) -> Optional[int]:
    if not value:
        return None

    match = re.search(r"\b(19|20)\d{2}\b", str(value))
    return int(match.group(0)) if match else None


def filter_papers_by_year(papers: Iterable[Paper], year: int) -> List[Paper]:
    return [paper for paper in papers if parse_year(paper.published_date) == year]
