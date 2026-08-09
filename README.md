# ResearchQuantize

ResearchQuantize is a production-focused Python CLI and library for aggregating research papers across:
- ArXiv
- PubMed
- Semantic Scholar

It is designed around reliable adapters, resilient parsing, deterministic tests, and straightforward CLI usage.

## Features

- Concurrent aggregation across multiple sources
- Optional source and year filters
- Deduplication with metadata-aware selection
- Export as table, JSON, or CSV
- SQLite persistence layer
- Deterministic unit tests (no network dependency)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the CLI:

```bash
python src/cli.py version
python src/cli.py aggregate --query "machine learning" --limit 10
python src/cli.py search --query "graph neural networks" --source arxiv --year 2024
python src/cli.py --format json --output results.json aggregate --query "NLP" --limit 20
```

## CLI Commands

```bash
python src/cli.py version
python src/cli.py aggregate --query "..." [--limit 10] [--sources arxiv pubmed semantic_scholar]
python src/cli.py search --query "..." [--source arxiv|pubmed|semantic_scholar] [--year 2024] [--limit 10]
```

Global options:

- `--format table|json|csv`
- `--output <file>`
- `--verbose`

## Project Structure

- `src/aggregator/core.py`: orchestration and concurrency
- `src/aggregator/sources/`: source adapters
- `src/aggregator/models/paper.py`: canonical paper model
- `src/aggregator/search/`: search entrypoints and filters
- `src/aggregator/database/`: SQLite storage
- `src/tests/`: deterministic test suite

## Environment Variables

Optional `.env` values:

```env
DEFAULT_QUERY_LIMIT=10
DEFAULT_SOURCE=arxiv
DEFAULT_YEAR_FILTER=
ARXIV_API_KEY=
PUBMED_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=
DATABASE_PATH=papers.db
LOG_LEVEL=INFO
```

## Testing

```bash
pytest -q
```

## Packaging

```bash
pip install .
researchquantize version
```

## License

MIT. See `LICENSE`.

<!-- architecture-atlas-v5:start -->
## Architecture Atlas v5

These editable Mermaid diagrams mirror the [Notion architecture dossier](https://app.notion.com/p/3b467342e8c181f3a49ac9d072ced5d2?pvs=204).

### 1. Federated-source anatomy

```mermaid
flowchart LR
  API["CLI / Python API"] --> QUERY["Canonical query model<br>terms, years, sources, fields and limits"]
  QUERY --> PLAN["Concurrent query planner"]
  PLAN --> RATE["Per-source rate limiter, pagination and retry policy"]
  RATE --> ARX["arXiv adapter"]
  RATE --> PUB["PubMed adapter"]
  RATE --> SEM["Semantic Scholar adapter"]
  ARX --> CANON["Canonical PaperRecord + field-level provenance"]
  PUB --> CANON
  SEM --> CANON
  CANON --> INDEX["Dedup candidate index<br>DOI, normalized title, authors, year"]
  INDEX --> MERGE["Deterministic merge policy"]
  MERGE --> FILTER["Source/year/field filters + stable sort"]
  FILTER --> DB[("SQLite literature library")]
  FILTER --> OUT["Table / JSON / CSV renderers"]
  RATE --> ERR[("Partial-source status, cursors, retry and error records")]
```

### 2. Deduplication wiring

```mermaid
flowchart TB
  RAW["Source-specific record"] --> PARSE["Adapter fixture-tested parser"] --> FIELD["Normalize DOI, title, authors, venue, year, abstract and URLs"]
  FIELD --> PROV["Attach source ID and provenance to every populated field"] --> CAND["Find candidate duplicates"]
  CAND --> DOI{"Exact normalized DOI match?"}
  DOI -->|yes| MERGE["Merge without discarding source identifiers"]
  DOI -->|no| SIM["Deterministic title/author/year similarity"] --> DECIDE{"Threshold and conflict policy"}
  DECIDE -->|same work| MERGE
  DECIDE -->|distinct / uncertain| KEEP["Keep separate and record uncertainty"]
  MERGE --> CANON["Canonical paper record"]
  KEEP --> CANON
  CANON --> PERSIST["SQLite + stable exports"]
```

### 3. Runtime narrative

```mermaid
sequenceDiagram
  actor User
  participant Q as Query Planner
  participant A as Source Adapters
  participant C as Canonicalizer / Deduper
  participant D as SQLite / Filters
  participant O as Output
  User->>Q: query, sources, years and limits
  Q->>A: concurrent paginated requests with source limits
  A-->>Q: records, cursors and explicit partial failures
  Q->>C: source records with provenance
  C->>C: normalize, generate duplicate candidates and apply merge policy
  C->>D: canonical records with retained source IDs
  D->>D: filter, persist and stable-sort
  D-->>O: table, JSON or CSV
  O-->>User: results plus completeness and source status
```

### 4. Reliability model

```mermaid
stateDiagram-v2
  [*] --> PLANNED
  PLANNED --> FETCHING
  FETCHING --> PARTIAL: one or more sources fail
  FETCHING --> NORMALIZING: all requested pages complete
  PARTIAL --> NORMALIZING: preserve partial-status evidence
  NORMALIZING --> DEDUPING --> FILTERING --> PERSISTED --> EXPORTED
```

<!-- architecture-atlas-v5:end -->
