SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    published_date TEXT,
    source TEXT,
    abstract TEXT,
    url TEXT,
    doi TEXT,
    keywords_json TEXT NOT NULL,
    citations INTEGER,
    journal TEXT,
    volume TEXT,
    issue TEXT,
    pages TEXT,
    pdf_url TEXT,
    arxiv_id TEXT,
    pubmed_id TEXT,
    semantic_scholar_id TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(title, source, doi, arxiv_id, pubmed_id)
);
"""
