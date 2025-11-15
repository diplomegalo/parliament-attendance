"""
Web scraping implementation for retrieving parliamentary session data.

This infrastructure adapter implements the repository interfaces using
web scraping technology (requests + BeautifulSoup).
"""

import requests
import logging
from datetime import datetime
from typing import List
from bs4 import BeautifulSoup

from domain.entities import SessionMetadata, SessionReference
from domain.repositories import ISessionMetadataRepository, IMinuteContentRetriever


class ParliamentarySessionScraper(ISessionMetadataRepository, IMinuteContentRetriever):
    """
    Session scraper adapter for Belgian parliament website.
    
    Implements both session metadata retrieval and content retrieval
    using HTTP requests and HTML parsing.
    """
    
    BASE_URL = "https://www.lachambre.be"
    LEGISLATURE_URL_TEMPLATE = (
        BASE_URL + "/kvvcr/showpage.cfm?"
        "section=/cricra&language=fr&cfm=dcricra.cfm?"
        "type=plen&cricra=CRI&count=all&legislat={legislature}"
    )
    
    def __init__(self, legislature: int = 56):
        """
        Initialize web scraper.
        
        Args:
            legislature: Legislature number (default 56)
        """
        self.logger = logging.getLogger(__name__)
        self.legislature = legislature
        self.legislature_url = self.LEGISLATURE_URL_TEMPLATE.format(
            legislature=legislature
        )
    
    def retrieve_all_sessions(self) -> List[SessionMetadata]:
        """
        Retrieve all session metadata from the parliamentary website.
        
        Scrapes the legislature listing page and extracts metadata
        for all available sessions.
        
        Returns:
            List of SessionMetadata objects
        """
        self.logger.info(
            f"Scraping session metadata for legislature {self.legislature}"
        )
        
        response = requests.get(self.legislature_url)
        if response.status_code != 200:
            raise Exception(
                f"HTTP error {response.status_code} "
                f"for legislature {self.legislature}"
            )
        
        page = BeautifulSoup(response.text, "html.parser")
        table = page.find("table", id="lst")
        
        if table is None:
            raise Exception("Session listing table not found")
        
        rows = table.find_all("tr", attrs={"valign": "top"})
        if not rows:
            self.logger.warning("No sessions found in table")
            return []
        
        sessions = []
        for row in rows:
            try:
                session = self._parse_session_row(row)
                if session:
                    sessions.append(session)
            except Exception as e:
                self.logger.warning(f"Failed to parse session row: {e}")
                continue
        
        self.logger.info(f"Scraped {len(sessions)} sessions")
        return sessions
    
    def _parse_session_row(self, row) -> SessionMetadata:
        """
        Parse a single table row into SessionMetadata.
        
        Args:
            row: BeautifulSoup row element
            
        Returns:
            SessionMetadata object or None if parsing fails
        """
        cells = row.find_all("td")
        if len(cells) < 5:
            return None
        
        # Extract reference
        ref_link = cells[0].find("a")
        if not ref_link:
            return None
        ref_value = ref_link.text.strip()
        
        # Extract description
        session_element = cells[1].find("i")
        if not session_element:
            return None
        description = session_element.text.strip()
        
        # Extract URL
        links = cells[3].find_all("a")
        if len(links) < 3:
            return None
        document_url = links[2]['href']
        
        # Extract and parse date
        date_str = cells[2].text.strip()
        session_date = self._parse_french_date(date_str)
        
        # Determine if provisional
        i_tag = cells[4].find("i")
        is_provisional = (
            i_tag is not None and
            i_tag.text.strip() == "version provisoire"
        )
        
        return SessionMetadata(
            reference=SessionReference(ref_value),
            date=session_date,
            description=description,
            document_url=document_url,
            is_provisional=is_provisional,
            legislature=self.legislature
        )
    
    def _parse_french_date(self, date_str: str) -> datetime:
        """
        Parse French date format (e.g., '14 novembre 2024').
        
        Args:
            date_str: Date string in French format
            
        Returns:
            datetime object
        """
        jour, mois, annee = date_str.split(" ", 2)
        mois_fr = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        return datetime(int(annee), mois_fr[mois.lower()], int(jour))
    
    def retrieve_content(self, document_url: str) -> str:
        """
        Retrieve full text content from a document URL.
        
        Args:
            document_url: Relative or absolute URL to minute document
            
        Returns:
            Full HTML/text content of the minute
        """
        # Ensure absolute URL
        if not document_url.startswith('http'):
            full_url = self.BASE_URL + document_url
        else:
            full_url = document_url
        
        self.logger.debug(f"Retrieving content from {full_url}")
        
        response = requests.get(full_url)
        if response.status_code != 200:
            raise Exception(f"HTTP error {response.status_code} for {full_url}")
        
        self.logger.debug(f"Retrieved {len(response.text)} characters")
        return response.text
