#!/usr/bin/env python3
"""ResearchQuantize command-line interface."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from rich.console import Console
from rich.table import Table

from aggregator.core import PaperAggregator
from aggregator.models.paper import Paper
from aggregator.search.engine import search_papers
from aggregator.utils.logger import setup_logger

VERSION = "2.0.0"

console = Console()
logger = setup_logger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate and search research papers across multiple academic sources."
    )
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table")
    parser.add_argument("--output", dest="output_file", help="Write output to file for json/csv")
    parser.add_argument("--verbose", "-v", action="store_true")

    subparsers = parser.add_subparsers(dest="command")

    version_parser = subparsers.add_parser("version", help="Show version info")
    version_parser.set_defaults(command="version")

    aggregate_parser = subparsers.add_parser("aggregate", help="Aggregate from one or more sources")
    aggregate_parser.add_argument("--query", "-q", required=True)
    aggregate_parser.add_argument("--limit", "-l", type=int, default=10)
    aggregate_parser.add_argument(
        "--sources",
        nargs="+",
        choices=["arxiv", "pubmed", "semantic_scholar"],
        help="Optional list of sources. Defaults to all.",
    )

    search_parser = subparsers.add_parser("search", help="Search with source/year filters")
    search_parser.add_argument("--query", "-q", required=True)
    search_parser.add_argument("--source", choices=["arxiv", "pubmed", "semantic_scholar"])
    search_parser.add_argument("--year", type=int)
    search_parser.add_argument("--limit", "-l", type=int, default=10)

    return parser


def _validate_args(args: argparse.Namespace) -> bool:
    if args.command in {"aggregate", "search"}:
        if not args.query or not args.query.strip():
            console.print("[red]Error: query cannot be empty.[/red]")
            return False

        if args.limit <= 0:
            console.print("[red]Error: limit must be greater than zero.[/red]")
            return False

    if args.command == "search" and args.year is not None:
        if args.year < 1900 or args.year > 2100:
            console.print("[red]Error: year must be between 1900 and 2100.[/red]")
            return False

    if args.output_file:
        output_path = Path(args.output_file)
        if output_path.parent != Path(".") and not output_path.parent.exists():
            console.print(f"[red]Error: output directory does not exist: {output_path.parent}[/red]")
            return False

    return True


def _display_results(papers: List[Paper], output_format: str, output_file: Optional[str]) -> None:
    if output_format == "table":
        _display_table(papers)
        return

    payload = [paper.to_dict() for paper in papers]

    if output_format == "json":
        content = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        content = _csv_content(papers)

    if output_file:
        with open(output_file, "w", encoding="utf-8", newline="" if output_format == "csv" else None) as f:
            f.write(content)
        console.print(f"[green]Wrote {len(papers)} papers to {output_file}[/green]")
    else:
        console.print(content)


def _display_table(papers: Iterable[Paper]) -> None:
    papers = list(papers)
    if not papers:
        console.print("[yellow]No papers found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title", width=60)
    table.add_column("Authors", width=30)
    table.add_column("Year", width=6)
    table.add_column("Source", width=18)

    for paper in papers:
        table.add_row(
            paper.title,
            paper.get_author_list_str(3),
            paper.get_publication_year(),
            paper.source or "unknown",
        )

    console.print(table)
    console.print(f"[bold green]Total papers: {len(papers)}[/bold green]")


def _csv_content(papers: List[Paper]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "title",
            "authors",
            "published_date",
            "source",
            "doi",
            "url",
            "citations",
            "journal",
        ]
    )

    for paper in papers:
        writer.writerow(
            [
                paper.title,
                "; ".join(paper.authors),
                paper.published_date or "",
                paper.source or "",
                paper.doi or "",
                paper.url or "",
                paper.citations if paper.citations is not None else "",
                paper.journal or "",
            ]
        )

    return buffer.getvalue()


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "version":
        console.print(f"ResearchQuantize {VERSION}")
        return 0

    if not _validate_args(args):
        return 1

    try:
        if args.command == "aggregate":
            aggregator = PaperAggregator()
            papers = aggregator.aggregate_papers_parallel(
                query=args.query,
                limit=args.limit,
                sources=args.sources,
            )
            _display_results(papers, args.format, args.output_file)
            return 0

        if args.command == "search":
            papers = search_papers(
                query=args.query,
                source=args.source,
                year=args.year,
                limit=args.limit,
            )
            _display_results(papers, args.format, args.output_file)
            return 0

        parser.print_help()
        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        return 130
    except Exception as exc:  # pragma: no cover - top-level fail-safe
        logger.exception("Unhandled CLI error")
        if args.verbose:
            raise
        console.print(f"[red]Error:[/red] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
