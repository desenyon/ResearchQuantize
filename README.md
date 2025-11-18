# ResearchQuantize

ResearchQuantize is a powerful CLI tool for aggregating and searching research papers from many academic sources like ArXiv, PubMed, and Semantic Scholar.

**Features:**

- **Parallel Processing**: Fast concurrent API calls for optimal performance
- **GUI Interface**: Modern Textual-based interactive interface
- **Database Storage**: SQLite database with full paper metadata

### Prerequisites

- Python 3.8 or higher
- `pip` (Python package manager)

### Quick Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/desenyon/ResearchQuantize.git
   cd ResearchQuantize
   ```
2. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
4. **Test the installation:**

   ```bash
   python src/cli.py version
   ```

### Optional Configuration

Environment variables (create `.env` file if needed):

```env
# Optional API keys (not required for basic usage)
PUBMED_API_KEY=your_key_here  # Only needed for >100 requests
SEMANTIC_SCHOLAR_API_KEY=your_key_here  # Optional for rate limiting
DATABASE_PATH=papers.db  # Custom database location
```

## Usage

### Quick Start

**Aggregate papers from all sources:**

```bash
python src/cli.py aggregate --query "machine learning" --limit 10
```

**Search with source filtering:**

```bash
python src/cli.py search --query "neural networks" --source arxiv --year 2024
```

**Export to JSON:**

```bash
python src/cli.py --format json --output results.json aggregate --query "AI" --limit 20
```

**Launch GUI:**

```bash
python src/cli.py gui
```

### Advanced Usage

**Multiple output formats:**

```bash
# Table format (default)
python src/cli.py aggregate --query "quantum computing"

# JSON export  
python src/cli.py --format json --output papers.json search --query "ML" --source semantic_scholar

# CSV export
python src/cli.py --format csv --output data.csv aggregate --query "deep learning" --limit 50
```

**Source-specific searches:**

```bash
# ArXiv only
python src/cli.py search --query "computer vision" --source arxiv

# PubMed only  
python src/cli.py search --query "cancer research" --source pubmed

# Semantic Scholar only
python src/cli.py search --query "NLP" --source semantic_scholar
```

**Year filtering:**

```bash
python src/cli.py search --query "AI ethics" --year 2024 --limit 15
```

### GUI Mode

Launch the interactive GUI for an enhanced user experience:

```bash
python src/cli.py gui
```

Features:

- Interactive search interface
- Real-time filtering options
- Beautiful results display
- Export capabilities

### Database Operations

ResearchQuantize automatically saves all papers to an SQLite database (`papers.db`).

**View saved papers:**

```bash
sqlite3 papers.db "SELECT title, authors, source FROM papers LIMIT 5;"
```

**Count papers by source:**

```bash
sqlite3 papers.db "SELECT source, COUNT(*) FROM papers GROUP BY source;"
```

**Export database to CSV:**

```bash
sqlite3 -header -csv papers.db "SELECT * FROM papers;" > all_papers.csv
```

## Architecture

### Supported Sources

- **ArXiv**  - Physics, mathematics, computer science preprints
- **PubMed**  - Medical and life science literature
- **Semantic Scholar**  - Academic papers with rich metadata and citations

## Configuration

### Preferences

Customize behavior via `src/config/preferences.json`:

```json
{
    "default_query_limit": 10,
    "default_source": "arxiv", 
    "default_year_filter": null,
    "theme": "dark",
    "show_advanced_options": false
}
```

### Environment Variables

Optional `.env` file configuration:

```env
# API Keys (optional)
PUBMED_API_KEY=your_key_here
SEMANTIC_SCHOLAR_API_KEY=your_key_here

# Database
DATABASE_PATH=papers.db

# Logging
LOG_LEVEL=INFO
```

## Testing

Run the test suite:

```bash
# All tests
python -m pytest src/tests/ -v

# Quick test
python -m pytest src/tests/ -q

# With coverage
python -m pytest src/tests/ --cov=src --cov-report=html
```

## Performance

**Benchmarks:**

- Parallel aggregation: ~16 papers in <1 second
- ArXiv: ~3 second rate limiting between requests
- Semantic Scholar: ~0.1 second rate limiting
- Deduplication: Advanced similarity matching with configurable thresholds

Database Schema

The SQLite database (`papers.db`) stores comprehensive paper metadata:

| Field                   | Type    | Description                                   |
| ----------------------- | ------- | --------------------------------------------- |
| `id`                  | INTEGER | Primary key                                   |
| `title`               | TEXT    | Paper title                                   |
| `authors`             | TEXT    | Comma-separated author list                   |
| `published_date`      | TEXT    | Publication date (ISO format)                 |
| `source`              | TEXT    | Data source (arxiv, pubmed, semantic_scholar) |
| `abstract`            | TEXT    | Paper abstract                                |
| `url`                 | TEXT    | Paper URL                                     |
| `doi`                 | TEXT    | Digital Object Identifier                     |
| `keywords`            | TEXT    | Comma-separated keywords                      |
| `citations`           | INTEGER | Citation count                                |
| `journal`             | TEXT    | Journal name                                  |
| `volume`              | TEXT    | Volume number                                 |
| `issue`               | TEXT    | Issue number                                  |
| `pages`               | TEXT    | Page range                                    |
| `pdf_url`             | TEXT    | PDF download URL                              |
| `arxiv_id`            | TEXT    | ArXiv identifier                              |
| `pubmed_id`           | TEXT    | PubMed identifier                             |
| `semantic_scholar_id` | TEXT    | Semantic Scholar identifier                   |
| `created_at`          | TEXT    | Record creation timestamp                     |

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Example Output

```bash
$ python src/cli.py aggregate --query "machine learning" --limit 5

╭─────────────────────────────────── Welcome ───────────────────────────────────╮
│                                                                               │
│  ResearchQuantize v1.1.0 - Aggregate and Search Research Papers               │
│                                                                               │
╰───────────────────────────────────────────────────────────────────────────────╯

Aggregating papers for query: machine learning
⠋ Fetching papers from multiple sources...

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Title                                          ┃ Authors                    ┃ Publish… ┃ Source     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Machine Learning Potential Repository          │ Atsuto Seko                │ 2020-07… │ ArXiv      │
│ Physics-informed machine learning              │ G. Karniadakis, I.         │ 2021-05… │ Semantic   │
│                                                │ Kevrekidis, Lu Lu          │          │ Scholar    │
│ TensorFlow: Large-Scale Machine Learning       │ Martín Abadi, Ashish       │ 2016-03… │ Semantic   │
│                                                │ Agarwal, P. Barham         │          │ Scholar    │
└────────────────────────────────────────────────┴────────────────────────────┴──────────┴────────────┘

Total papers found: 10

  Paper Sources Statistics  
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Source           ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ ArXiv            │     5 │
│ Semantic Scholar │     5 │
└──────────────────┴───────┘
```
