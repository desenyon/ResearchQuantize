# src/config/settings.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file and so
load_dotenv()

# Default configuration settings
DEFAULT_QUERY_LIMIT = 10
DEFAULT_SOURCE = "arxiv"
DEFAULT_YEAR_FILTER = None

# API keys and other sensitive information
ARXIV_API_KEY = os.getenv("ARXIV_API_KEY", "")
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

# Database path
DATABASE_PATH = os.getenv("DATABASE_PATH", "papers.db")