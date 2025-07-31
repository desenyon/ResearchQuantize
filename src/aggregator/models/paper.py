# src/aggregator/models/paper.py

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class Paper:
    """
    Enhanced Paper model with validation and additional metadata.
    """
    title: str
    authors: List[str] = field(default_factory=list)
    published_date: Optional[str] = None
    source: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    citations: Optional[int] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    pdf_url: Optional[str] = None
    arxiv_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    semantic_scholar_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate and clean data after initialization."""
        # Clean title
        if self.title:
            self.title = self.title.strip()
        else:
            raise ValueError("Paper title cannot be empty")
        
        # Clean authors
        if self.authors:
            self.authors = [author.strip() for author in self.authors if author.strip()]
        
        # Clean abstract
        if self.abstract:
            self.abstract = self.abstract.strip()
        
        # Validate URLs
        if self.url and not self._is_valid_url(self.url):
            self.url = None
        
        if self.pdf_url and not self._is_valid_url(self.pdf_url):
            self.pdf_url = None
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Validate URL format."""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Paper to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if key == 'created_at':
                result[key] = value.isoformat() if value else None
            elif isinstance(value, list):
                result[key] = value if value else []
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        """Create Paper from dictionary."""
        # Handle datetime conversion
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Filter out unknown fields
        valid_fields = set(cls.__dataclass_fields__.keys())
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    def to_json(self) -> str:
        """Convert Paper to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Paper':
        """Create Paper from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_primary_author(self) -> str:
        """Get the first author or 'Unknown' if no authors."""
        return self.authors[0] if self.authors else "Unknown"
    
    def get_author_list_str(self, max_authors: int = 3) -> str:
        """Get formatted author string."""
        if not self.authors:
            return "Unknown"
        
        if len(self.authors) <= max_authors:
            return ", ".join(self.authors)
        else:
            return f"{', '.join(self.authors[:max_authors])}, et al."
    
    def get_formatted_citation(self) -> str:
        """Get formatted citation string."""
        authors = self.get_author_list_str()
        year = self.get_publication_year()
        title = self.title
        
        citation = f"{authors} ({year}). {title}."
        
        if self.journal:
            citation += f" {self.journal}"
            if self.volume:
                citation += f", {self.volume}"
                if self.issue:
                    citation += f"({self.issue})"
            if self.pages:
                citation += f", {self.pages}"
        
        if self.doi:
            citation += f" DOI: {self.doi}"
        
        return citation
    
    def get_publication_year(self) -> str:
        """Extract year from published_date."""
        if not self.published_date:
            return "Unknown"
        
        # Try to extract year from various date formats
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', str(self.published_date))
        return year_match.group() if year_match else "Unknown"
    
    def has_pdf(self) -> bool:
        """Check if paper has PDF URL."""
        return bool(self.pdf_url)
    
    def is_recent(self, years: int = 5) -> bool:
        """Check if paper is published within specified years."""
        try:
            year = int(self.get_publication_year())
            current_year = datetime.now().year
            return (current_year - year) <= years
        except (ValueError, TypeError):
            return False
    
    def get_source_icon(self) -> str:
        """Get Unicode icon for source."""
        icons = {
            'arxiv': '📄',
            'pubmed': '🏥',
            'semantic_scholar': '🎓',
            'unknown': '📋'
        }
        source_lower = (self.source or 'unknown').lower()
        return icons.get(source_lower, icons['unknown'])
    
    def __str__(self) -> str:
        """String representation for display."""
        return f"{self.get_source_icon()} {self.title} - {self.get_author_list_str()} ({self.get_publication_year()})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"Paper(title='{self.title[:50]}...', "
                f"authors={len(self.authors)}, "
                f"source='{self.source}', "
                f"year='{self.get_publication_year()}')")
    
    def __eq__(self, other) -> bool:
        """Check equality based on title and primary author."""
        if not isinstance(other, Paper):
            return False
        return (self.title.lower() == other.title.lower() and 
                self.get_primary_author().lower() == other.get_primary_author().lower())
    
    def __hash__(self) -> int:
        """Hash based on title for use in sets."""
        return hash(self.title.lower() if self.title else "")