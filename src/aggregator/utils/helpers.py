# src/aggregator/utils/helpers.py

from datetime import datetime
from typing import List, Set, Dict, Any
import re
from difflib import SequenceMatcher
from ..models.paper import Paper
from ..utils.logger import setup_logger

logger = setup_logger()

def format_date(date_str: str) -> str:
    """
    Format a date string into a more readable format.
    
    Args:
        date_str (str): The date string to format.
    
    Returns:
        str: The formatted date string.
    """
    if not date_str:
        return "Unknown"
        
    try:
        # Try multiple date formats
        formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y", "%Y-%m"]
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str[:len(fmt)], fmt)
                return date_obj.strftime("%B %d, %Y") if fmt != "%Y" else str(date_obj.year)
            except ValueError:
                continue
        return date_str
    except Exception:
        return date_str

def clean_string(text: str) -> str:
    """
    Clean a string by removing extra whitespace and special characters.
    
    Args:
        text (str): The string to clean.
    
    Returns:
        str: The cleaned string.
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text

def similarity_score(str1: str, str2: str) -> float:
    """
    Calculate similarity score between two strings.
    
    Args:
        str1 (str): First string
        str2 (str): Second string
        
    Returns:
        float: Similarity score between 0 and 1
    """
    if not str1 or not str2:
        return 0.0
    
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def normalize_title(title: str) -> str:
    """
    Normalize a paper title for comparison.
    
    Args:
        title (str): Paper title
        
    Returns:
        str: Normalized title
    """
    if not title:
        return ""
    
    # Convert to lowercase and remove punctuation
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized.strip())
    
    return normalized

def deduplicate_papers(papers: List[Paper], similarity_threshold: float = 0.85) -> List[Paper]:
    """
    Remove duplicate papers based on title similarity.
    
    Args:
        papers (List[Paper]): List of papers to deduplicate
        similarity_threshold (float): Threshold for considering papers as duplicates
        
    Returns:
        List[Paper]: Deduplicated list of papers
    """
    if not papers:
        return []
    
    unique_papers = []
    seen_titles = set()
    
    for paper in papers:
        if not paper.title:
            continue
            
        normalized_title = normalize_title(paper.title)
        
        # Check if we've seen a similar title
        is_duplicate = False
        for seen_title in seen_titles:
            if similarity_score(normalized_title, seen_title) >= similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_papers.append(paper)
            seen_titles.add(normalized_title)
    
    logger.info(f"Deduplication: {len(papers)} -> {len(unique_papers)} papers")
    return unique_papers

def merge_papers_by_similarity(papers: List[Paper], similarity_threshold: float = 0.95) -> List[Paper]:
    """
    Merge similar papers by combining their information.
    
    Args:
        papers (List[Paper]): List of papers to merge
        similarity_threshold (float): Threshold for merging papers
        
    Returns:
        List[Paper]: List with merged papers
    """
    if not papers:
        return []
    
    merged_papers = []
    processed = set()
    
    for i, paper in enumerate(papers):
        if i in processed:
            continue
            
        # Find similar papers
        similar_papers = [paper]
        for j, other_paper in enumerate(papers[i+1:], i+1):
            if j in processed:
                continue
                
            if similarity_score(normalize_title(paper.title), 
                              normalize_title(other_paper.title)) >= similarity_threshold:
                similar_papers.append(other_paper)
                processed.add(j)
        
        # Merge information from similar papers
        merged_paper = _merge_paper_info(similar_papers)
        merged_papers.append(merged_paper)
        processed.add(i)
    
    return merged_papers

def _merge_paper_info(papers: List[Paper]) -> Paper:
    """
    Merge information from multiple similar papers.
    
    Args:
        papers (List[Paper]): Papers to merge
        
    Returns:
        Paper: Merged paper with combined information
    """
    if not papers:
        raise ValueError("Cannot merge empty list of papers")
    
    if len(papers) == 1:
        return papers[0]
    
    # Use the first paper as base
    base_paper = papers[0]
    
    # Combine authors from all papers
    all_authors = set()
    for paper in papers:
        if paper.authors:
            all_authors.update(paper.authors)
    
    # Use the most complete title
    best_title = max(papers, key=lambda p: len(p.title or "")).title
    
    # Use the most recent date
    best_date = None
    for paper in papers:
        if paper.published_date:
            if not best_date or paper.published_date > best_date:
                best_date = paper.published_date
    
    # Combine sources
    sources = [p.source for p in papers if p.source]
    combined_source = ", ".join(set(sources)) if sources else base_paper.source
    
    return Paper(
        title=best_title,
        authors=list(all_authors),
        published_date=best_date or base_paper.published_date,
        source=combined_source
    )

def validate_paper_data(paper_data: Dict[str, Any]) -> bool:
    """
    Validate paper data before creating Paper object.
    
    Args:
        paper_data (Dict): Paper data dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['title']
    
    for field in required_fields:
        if not paper_data.get(field):
            return False
    
    return True

def extract_keywords_from_title(title: str) -> List[str]:
    """
    Extract potential keywords from paper title.
    
    Args:
        title (str): Paper title
        
    Returns:
        List[str]: List of keywords
    """
    if not title:
        return []
    
    # Common stop words to exclude
    stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'via', 'using', 'based', 'new', 'novel'
    }
    
    # Extract words, remove punctuation and filter
    words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
    keywords = [word for word in words if word not in stop_words]
    
    return keywords[:10]  # Return top 10 keywords