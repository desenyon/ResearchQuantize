# src/aggregator/database/manager.py

import sqlite3
from typing import List
from ..models.paper import Paper
from ..utils.logger import setup_logger

logger = setup_logger()

class DatabaseManager:
    def __init__(self, db_path="papers.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    authors TEXT,
                    published_date TEXT,
                    source TEXT,
                    abstract TEXT,
                    url TEXT,
                    doi TEXT,
                    keywords TEXT,
                    citations INTEGER,
                    journal TEXT,
                    volume TEXT,
                    issue TEXT,
                    pages TEXT,
                    pdf_url TEXT,
                    arxiv_id TEXT,
                    pubmed_id TEXT,
                    semantic_scholar_id TEXT,
                    created_at TEXT
                )
            """)
            self.conn.commit()
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def save_paper(self, paper):
        """
        Save a paper to the database.
        
        Args:
            paper (Paper): The Paper object to save.
        """
        if not self.conn:
            logger.error("Database connection not established.")
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO papers (
                    title, authors, published_date, source, abstract, url, doi, 
                    keywords, citations, journal, volume, issue, pages, pdf_url,
                    arxiv_id, pubmed_id, semantic_scholar_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper.title,
                ", ".join(paper.authors) if paper.authors else "",
                paper.published_date,
                paper.source,
                paper.abstract,
                paper.url,
                paper.doi,
                ", ".join(paper.keywords) if paper.keywords else "",
                paper.citations,
                paper.journal,
                paper.volume,
                paper.issue,
                paper.pages,
                paper.pdf_url,
                paper.arxiv_id,
                paper.pubmed_id,
                paper.semantic_scholar_id,
                paper.created_at.isoformat() if paper.created_at else None
            ))
            self.conn.commit()
            logger.info(f"Saved paper '{paper.title}' to the database.")
        except Exception as e:
            logger.error(f"Error saving paper to database: {e}")

    def get_all_papers(self):
        """
        Retrieve all papers from the database.
        
        Returns:
            list: A list of Paper objects.
        """
        if not self.conn:
            logger.error("Database connection not established.")
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT title, authors, published_date, source, abstract, url, doi,
                       keywords, citations, journal, volume, issue, pages, pdf_url,
                       arxiv_id, pubmed_id, semantic_scholar_id, created_at
                FROM papers
            """)
            rows = cursor.fetchall()
            papers = []
            
            for row in rows:
                try:
                    (title, authors, published_date, source, abstract, url, doi,
                     keywords, citations, journal, volume, issue, pages, pdf_url,
                     arxiv_id, pubmed_id, semantic_scholar_id, created_at) = row
                    
                    # Parse authors and keywords back to lists
                    author_list = [a.strip() for a in authors.split(", ") if a.strip()] if authors else []
                    keyword_list = [k.strip() for k in keywords.split(", ") if k.strip()] if keywords else []
                    
                    # Create Paper object
                    paper = Paper(
                        title=title,
                        authors=author_list,
                        published_date=published_date,
                        source=source,
                        abstract=abstract,
                        url=url,
                        doi=doi,
                        keywords=keyword_list,
                        citations=citations,
                        journal=journal,
                        volume=volume,
                        issue=issue,
                        pages=pages,
                        pdf_url=pdf_url,
                        arxiv_id=arxiv_id,
                        pubmed_id=pubmed_id,
                        semantic_scholar_id=semantic_scholar_id
                    )
                    papers.append(paper)
                    
                except Exception as paper_error:
                    logger.warning(f"Error creating paper object from database row: {paper_error}")
                    continue
                    
            logger.info(f"Retrieved {len(papers)} papers from database.")
            return papers
            
        except Exception as e:
            logger.error(f"Error retrieving papers from database: {e}")
            return []

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed.")

    def get_papers_by_source(self, source: str):
        """
        Retrieve papers from a specific source.
        
        Args:
            source (str): The source to filter by.
            
        Returns:
            list: A list of Paper objects from the specified source.
        """
        if not self.conn:
            logger.error("Database connection not established.")
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT title, authors, published_date, source, abstract, url, doi,
                       keywords, citations, journal, volume, issue, pages, pdf_url,
                       arxiv_id, pubmed_id, semantic_scholar_id, created_at
                FROM papers WHERE source = ?
            """, (source,))
            rows = cursor.fetchall()
            papers = []
            
            for row in rows:
                try:
                    (title, authors, published_date, source, abstract, url, doi,
                     keywords, citations, journal, volume, issue, pages, pdf_url,
                     arxiv_id, pubmed_id, semantic_scholar_id, created_at) = row
                    
                    author_list = [a.strip() for a in authors.split(", ") if a.strip()] if authors else []
                    keyword_list = [k.strip() for k in keywords.split(", ") if k.strip()] if keywords else []
                    
                    paper = Paper(
                        title=title,
                        authors=author_list,
                        published_date=published_date,
                        source=source,
                        abstract=abstract,
                        url=url,
                        doi=doi,
                        keywords=keyword_list,
                        citations=citations,
                        journal=journal,
                        volume=volume,
                        issue=issue,
                        pages=pages,
                        pdf_url=pdf_url,
                        arxiv_id=arxiv_id,
                        pubmed_id=pubmed_id,
                        semantic_scholar_id=semantic_scholar_id
                    )
                    papers.append(paper)
                    
                except Exception as paper_error:
                    logger.warning(f"Error creating paper object from database row: {paper_error}")
                    continue
                    
            logger.info(f"Retrieved {len(papers)} papers from source '{source}'.")
            return papers
            
        except Exception as e:
            logger.error(f"Error retrieving papers by source from database: {e}")
            return []

    def count_papers(self) -> int:
        """
        Count total number of papers in the database.
        
        Returns:
            int: Number of papers in the database.
        """
        if not self.conn:
            logger.error("Database connection not established.")
            return 0
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM papers")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Error counting papers in database: {e}")
            return 0

    def paper_exists(self, title: str, authors: List[str]) -> bool:
        """
        Check if a paper already exists in the database.
        
        Args:
            title (str): Paper title.
            authors (List[str]): List of authors.
            
        Returns:
            bool: True if paper exists, False otherwise.
        """
        if not self.conn:
            logger.error("Database connection not established.")
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM papers 
                WHERE title = ? AND authors = ?
            """, (title, ", ".join(authors) if authors else ""))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"Error checking if paper exists: {e}")
            return False