# src/aggregator/sources/pubmed.py

import requests
from ..models.paper import Paper
from ..utils.logger import setup_logger

logger = setup_logger()

class PubmedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    def fetch_papers(self, query, limit=10):
        """
        Fetch papers from PubMed based on the query.
        
        Args:
            query (str): The search query.
            limit (int): Maximum number of papers to retrieve.
        
        Returns:
            list: A list of Paper objects.
        """
        logger.info(f"Fetching papers from PubMed for query: {query}")
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': limit,
            'usehistory': 'y',
            'tool': 'PaperEngine',
            'email': 'your_email@example.com'
        }

        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()

        # Parse the XML response (for simplicity, assume we have a helper function)
        papers = self._parse_response(response.text)
        logger.info(f"Fetched {len(papers)} papers from PubMed.")
        return papers

    def _parse_response(self, xml_data):
        """
        Parse the PubMed API response and return a list of Paper objects.
        
        Args:
            xml_data (str): The XML response from PubMed.
        
        Returns:
            list: A list of Paper objects.
        """
        # Simplified parsing logic (you can use an XML parser like lxml or xml.etree.ElementTree)
        papers = []
        # Example: Assume we parse the XML and extract title, authors, etc.
        for entry in xml_data.split('<DocSum>')[1:]:
            title = entry.split('<Item Name="Title">')[1].split('</Item>')[0]
            authors = [author.split('<Author>')[1].split('</Author>')[0] for author in entry.split('<AuthorList>')[1:]]
            published_date = entry.split('<PubDate>')[1].split('</PubDate>')[0]
            papers.append(Paper(title=title, authors=authors, published_date=published_date, source="PubMed"))
        
        return papers