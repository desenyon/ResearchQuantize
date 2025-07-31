#!/usr/bin/env python3
"""
ResearchQuantize CLI - Advanced command-line interface for research paper aggregation and search.

This module provides a rich, inte                        yield Checkbox("Semantic Scholar", False, id="semantic")ctive CLI for searching and aggregating research papers
from multiple academic sources including ArXiv, PubMed, and Semantic Scholar.

Features:
- Multiple output formats (table, JSON, CSV)
- Progress indicators and rich console output
- Advanced filtering and validation
- Export capabilities
- Beautiful GUI interface using Textual
- Error handling and logging
"""

import argparse
import json
import csv
import sys
import asyncio
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm
from rich.layout import Layout
from rich.align import Align

# Import GUI components
try:
    from textual.app import App
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import (Header, Footer, Input, Button, DataTable, 
                                Static, ProgressBar, Label, Select, Checkbox)
    from textual.screen import Screen
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Note: GUI features unavailable. Install 'textual' for advanced interface.")

try:
    from aggregator.core import aggregate_papers, PaperAggregator
    from aggregator.search.engine import search_papers
    from aggregator.utils.logger import setup_logger
    from aggregator.models.paper import Paper
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)

# Constants
VERSION = "1.1.0"
SUPPORTED_SOURCES = ['arxiv', 'pubmed', 'semantic_scholar']
OUTPUT_FORMATS = ['table', 'json', 'csv', 'gui']

# Initialize Rich console and logger
console = Console()
logger = setup_logger()

# GUI Application Classes
if GUI_AVAILABLE:
    class PaperResultsScreen(Screen):
        """Screen for displaying paper search results."""
        
        def __init__(self, papers: List[Paper], search_query: str):
            super().__init__()
            self.papers = papers
            self.search_query = search_query
        
        def compose(self):
            yield Header()
            with Container():
                yield Static(f"Search Results for: '{self.search_query}' ({len(self.papers)} papers)", id="results-title")
                
                # Create data table
                table = DataTable()
                table.add_columns("Title", "Authors", "Year", "Source", "Citations")
                
                for paper in self.papers:
                    table.add_row(
                        paper.title[:50] + "..." if len(paper.title) > 50 else paper.title,
                        paper.get_author_list_str(2),
                        paper.get_publication_year(),
                        paper.source or "Unknown",
                        str(paper.citations) if paper.citations else "N/A"
                    )
                
                yield table
                
                with Horizontal():
                    yield Button("Export JSON", id="export-json")
                    yield Button("Export CSV", id="export-csv")
                    yield Button("New Search", id="new-search")
                    yield Button("Exit", id="exit")
            
            yield Footer()
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "export-json":
                self._export_json()
            elif event.button.id == "export-csv":
                self._export_csv()
            elif event.button.id == "new-search":
                self.app.push_screen(SearchScreen())
            elif event.button.id == "exit":
                self.app.exit()
        
        def _export_json(self):
            """Export results to JSON file."""
            filename = f"search_results_{self.search_query.replace(' ', '_')}.json"
            papers_data = [paper.to_dict() for paper in self.papers]
            with open(filename, 'w') as f:
                json.dump(papers_data, f, indent=2)
            self.notify(f"Results exported to {filename}")
        
        def _export_csv(self):
            """Export results to CSV file."""
            filename = f"search_results_{self.search_query.replace(' ', '_')}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Title", "Authors", "Year", "Source", "Citations", "Abstract"])
                for paper in self.papers:
                    writer.writerow([
                        paper.title,
                        "; ".join(paper.authors),
                        paper.get_publication_year(),
                        paper.source,
                        paper.citations or "",
                        paper.abstract or ""
                    ])
            self.notify(f"Results exported to {filename}")

    class SearchScreen(Screen):
        """Main search interface screen."""
        
        def compose(self):
            yield Header()
            with Container():
                yield Static("🔬 ResearchQuantize - Advanced Paper Search", id="app-title")
                
                with Vertical():
                    yield Label("Search Query:")
                    yield Input(placeholder="Enter your search query...", id="search-input")
                    
                    yield Label("Search Type:")
                    yield Select([
                        ("aggregate", "Aggregate from all sources"),
                        ("search", "Targeted search")
                    ], id="search-type")
                    
                    yield Label("Sources:")
                    with Horizontal():
                        yield Checkbox("ArXiv", True, id="arxiv")
                        yield Checkbox("PubMed", True, id="pubmed")
                        yield Checkbox("Semantic Scholar", True, id="semantic")
                        yield Checkbox("Google Scholar", False, id="google")
                    
                    yield Label("Limit:")
                    yield Input(placeholder="10", id="limit-input")
                    
                    with Horizontal():
                        yield Button("Search", variant="primary", id="search-btn")
                        yield Button("Clear", id="clear-btn")
                        yield Button("Exit", id="exit-btn")
                    
                    yield Static("", id="status")
            
            yield Footer()
        
        async def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "search-btn":
                await self._perform_search()
            elif event.button.id == "clear-btn":
                self._clear_inputs()
            elif event.button.id == "exit-btn":
                self.app.exit()
        
        async def _perform_search(self):
            """Perform the search operation."""
            # Get inputs
            query_input = self.query_one("#search-input", Input)
            search_type = self.query_one("#search-type", Select)
            limit_input = self.query_one("#limit-input", Input)
            status = self.query_one("#status", Static)
            
            query = query_input.value.strip()
            if not query:
                status.update("Please enter a search query.")
                return
            
            try:
                limit = int(limit_input.value) if limit_input.value else 10
            except ValueError:
                limit = 10
            
            # Get selected sources
            sources = []
            if self.query_one("#arxiv", Checkbox).value:
                sources.append("arxiv")
            if self.query_one("#pubmed", Checkbox).value:
                sources.append("pubmed")
            if self.query_one("#semantic", Checkbox).value:
                sources.append("semantic_scholar")
            
            if not sources:
                status.update("Please select at least one source.")
                return
            
            # Show progress
            status.update(f"Searching for '{query}'...")
            
            try:
                # Perform search in background
                if search_type.value == "aggregate":
                    aggregator = PaperAggregator()
                    papers = aggregator.aggregate_papers_parallel(query, limit, sources)
                else:
                    papers = search_papers(query, source=None, year=None)[:limit]
                
                if papers:
                    # Switch to results screen
                    self.app.push_screen(PaperResultsScreen(papers, query))
                else:
                    status.update("No papers found for your query.")
                    
            except Exception as e:
                status.update(f"Error: {str(e)}")
                logger.error(f"Search error: {str(e)}")
        
        def _clear_inputs(self):
            """Clear all input fields."""
            self.query_one("#search-input", Input).value = ""
            self.query_one("#limit-input", Input).value = ""
            self.query_one("#status", Static).update("")

    class ResearchQuantizeApp(App):
        """Main Textual application."""
        
        CSS = """
        #app-title {
            text-align: center;
            color: $primary;
            text-style: bold;
            margin: 1;
        }
        
        #results-title {
            text-align: center;
            color: $secondary;
            text-style: bold;
            margin: 1;
        }
        
        Button {
            margin: 1;
        }
        
        Input {
            margin: 1;
        }
        
        Label {
            margin-top: 1;
            text-style: bold;
        }
        
        DataTable {
            margin: 1;
        }
        
        Checkbox {
            margin: 1;
        }
        """
        
        TITLE = "ResearchQuantize"
        SUB_TITLE = "Advanced Research Paper Aggregation"
        
        def on_mount(self):
            self.push_screen(SearchScreen())

def launch_gui():
    """Launch the GUI interface."""
    if not GUI_AVAILABLE:
        console.print("[red]GUI not available. Please install 'textual' package.[/red]")
        return False
    
    app = ResearchQuantizeApp()
    app.run()
    return True

def display_results(papers: List[Paper], output_format: str = "table", output_file: Optional[str] = None):
    """Display search results in various formats."""
    if not papers:
        console.print("[yellow]No papers found for the given query.[/yellow]")
        return
    
    if output_format == "table":
        _display_table(papers)
    elif output_format == "json":
        _display_json(papers, output_file)
    elif output_format == "csv":
        _display_csv(papers, output_file)
    else:
        console.print(f"[red]Unsupported output format: {output_format}[/red]")

def _display_table(papers: List[Paper]):
    """Display papers in a rich table format."""
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("Title", style="dim", width=50, no_wrap=False)
    table.add_column("Authors", style="cyan", width=30)
    table.add_column("Published", style="green", width=12)
    table.add_column("Source", style="yellow", width=15)

    for paper in papers:
        # Handle potential None values gracefully
        title = paper.title or "N/A"
        authors = ", ".join(paper.authors) if paper.authors else "N/A"
        published_date = paper.published_date or "N/A"
        source = paper.source or "N/A"
        
        table.add_row(title, authors, published_date, source)

    console.print(table)
    console.print(f"\n[bold green]Total papers found: {len(papers)}[/bold green]")
    
    # Display additional statistics
    display_stats(papers)

def _display_json(papers: List[Paper], output_file: Optional[str] = None):
    """Display papers in JSON format."""
    papers_data = []
    for paper in papers:
        papers_data.append({
            "title": paper.title,
            "authors": paper.authors,
            "published_date": paper.published_date,
            "source": paper.source
        })
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers_data, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Results saved to {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving to file: {e}[/red]")
    else:
        console.print_json(data=papers_data)

def _display_csv(papers: List[Paper], output_file: Optional[str] = None):
    """Display papers in CSV format."""
    import io
    from contextlib import redirect_stdout
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Title", "Authors", "Published Date", "Source"])
    
    for paper in papers:
        writer.writerow([
            paper.title or "",
            "; ".join(paper.authors) if paper.authors else "",
            paper.published_date or "",
            paper.source or ""
        ])
    
    csv_content = output.getvalue()
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_content)
            console.print(f"[green]Results saved to {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving to file: {e}[/red]")
    else:
        console.print(csv_content)

def validate_args(args):
    """Validate command line arguments."""
    if args.command in ['aggregate', 'search']:
        if not args.query or not args.query.strip():
            console.print("[red]Error: Query cannot be empty.[/red]")
            return False
        
        if args.command == 'aggregate' and args.limit <= 0:
            console.print("[red]Error: Limit must be a positive integer.[/red]")
            return False
            
        if hasattr(args, 'year') and args.year:
            current_year = 2025  # Based on context date
            if args.year < 1900 or args.year > current_year:
                console.print(f"[red]Error: Year must be between 1900 and {current_year}.[/red]")
                return False
                
        if hasattr(args, 'output_file') and args.output_file:
            output_path = Path(args.output_file)
            if not output_path.parent.exists():
                console.print(f"[red]Error: Directory {output_path.parent} does not exist.[/red]")
                return False
    
    return True

def display_welcome():
    """Display welcome message and app info."""
    welcome_text = Text()
    welcome_text.append("ResearchQuantize", style="bold blue")
    welcome_text.append(f" v{VERSION}", style="dim")
    welcome_text.append(" - Aggregate and Search Research Papers", style="dim")
    
    panel = Panel(
        welcome_text,
        title="Welcome",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)

def display_stats(papers: List[Paper]):
    """Display statistics about the retrieved papers."""
    if not papers:
        return
    
    # Count papers by source
    source_counts = {}
    for paper in papers:
        source = paper.source or "Unknown"
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Create stats table
    stats_table = Table(title="Paper Sources Statistics", show_header=True, header_style="bold cyan")
    stats_table.add_column("Source", style="yellow")
    stats_table.add_column("Count", style="green", justify="right")
    
    for source, count in sorted(source_counts.items()):
        stats_table.add_row(source, str(count))
    
    console.print("\n", stats_table)

def save_query_history(query: str, command: str, results_count: int):
    """Save query to history file for future reference."""
    try:
        history_file = Path.home() / ".researchquantize_history.json"
        history = []
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        from datetime import datetime
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "query": query,
            "results_count": results_count
        }
        
        history.append(entry)
        
        # Keep only last 100 entries
        if len(history) > 100:
            history = history[-100:]
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        logger.warning(f"Could not save query history: {e}")

def create_version_command(parser):
    """Add version command to parser."""
    version_parser = parser.add_parser('version', help='Show version information')
    return version_parser

def main():
    """Main CLI entry point with enhanced features."""
    display_welcome()
    
    # Set up argument parser with better organization
    parser = argparse.ArgumentParser(
        description="ResearchQuantize: Aggregate and Search Research Papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s aggregate --query "machine learning" --limit 20
  %(prog)s search --query "neural networks" --source arxiv --year 2024
  %(prog)s search --query "covid-19" --format json --output results.json
        """
    )
    
    # Global arguments
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table',
                       help='Output format (default: table)')
    parser.add_argument('--output', '-o', dest='output_file', 
                       help='Output file path (for json/csv formats)')
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Version command
    create_version_command(subparsers)

    # GUI command
    gui_parser = subparsers.add_parser(
        'gui', 
        help='Launch beautiful GUI interface',
        description='Launch an interactive graphical interface for paper search and management'
    )

    # Aggregation command with enhanced options
    aggregate_parser = subparsers.add_parser(
        'aggregate', 
        help='Aggregate research papers from multiple sources',
        description='Fetch papers from ArXiv, PubMed, and Semantic Scholar'
    )
    aggregate_parser.add_argument('--query', '-q', required=True, 
                                help='Search query for papers')
    aggregate_parser.add_argument('--limit', '-l', type=int, default=10, 
                                help='Limit the number of results per source (default: 10)')
    aggregate_parser.add_argument('--no-confirm', action='store_true',
                                help='Skip confirmation prompts')

    # Search command with enhanced filtering
    search_parser = subparsers.add_parser(
        'search', 
        help='Search for specific papers with advanced filtering',
        description='Search papers with filtering options by source and year'
    )
    search_parser.add_argument('--query', '-q', required=True, 
                             help='Search query for papers')
    search_parser.add_argument('--source', '-s', 
                             choices=['arxiv', 'pubmed', 'semantic_scholar'], 
                             help='Filter by specific source')
    search_parser.add_argument('--year', '-y', type=int, 
                             help='Filter by publication year')
    search_parser.add_argument('--limit', '-l', type=int, default=50,
                             help='Maximum number of results (default: 50)')

    # Parse arguments
    args = parser.parse_args()

    # Handle GUI command
    if args.command == 'gui':
        if launch_gui():
            return
        else:
            console.print("[yellow]Falling back to command-line interface...[/yellow]")
            parser.print_help()
            return

    # Handle no command case
    if not args.command:
        parser.print_help()
        return
    
    # Handle version command
    if args.command == 'version':
        console.print(f"[bold blue]ResearchQuantize[/bold blue] version [green]{VERSION}[/green]")
        console.print("A command-line tool for aggregating and searching research papers.")
        console.print(f"Supported sources: {', '.join(SUPPORTED_SOURCES)}")
        console.print(f"Output formats: {', '.join(OUTPUT_FORMATS)}")
        return

    # Validate arguments
    if not validate_args(args):
        sys.exit(1)

    try:
        if args.command == 'aggregate':
            # Show confirmation for large requests
            if args.limit > 20 and not args.no_confirm:
                if not Confirm.ask(f"You're requesting {args.limit} papers per source. This might take a while. Continue?"):
                    console.print("[yellow]Operation cancelled.[/yellow]")
                    return

            logger.info(f"Aggregating papers for query: {args.query}")
            console.print(f"[blue]Aggregating papers for query:[/blue] [bold]{args.query}[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Fetching papers from multiple sources...", total=None)
                papers = aggregate_papers(args.query, limit=args.limit)
                progress.update(task, completed=100)

            display_results(papers, args.format, args.output_file)
            save_query_history(args.query, "aggregate", len(papers))

        elif args.command == 'search':
            logger.info(f"Searching papers for query: {args.query}")
            console.print(f"[blue]Searching papers for query:[/blue] [bold]{args.query}[/bold]")
            
            # Display filter info
            if args.source:
                console.print(f"[dim]Filtering by source: {args.source}[/dim]")
            if args.year:
                console.print(f"[dim]Filtering by year: {args.year}[/dim]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Searching papers...", total=None)
                papers = search_papers(
                    args.query, 
                    source=args.source, 
                    year=args.year
                )
                progress.update(task, completed=100)

            display_results(papers, args.format, args.output_file)
            save_query_history(args.query, "search", len(papers))

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        if args.verbose:
            console.print_exception()
        else:
            console.print(f"[red]Error: {str(e)}[/red]")
            console.print("[dim]Use --verbose for detailed error information.[/dim]")
        sys.exit(1)

if __name__ == "__main__":
    main()