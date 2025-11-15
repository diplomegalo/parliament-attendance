"""
Member Scraper interface.

Defines how to scrape parliament member data from external sources.
"""

from abc import ABC, abstractmethod
from typing import List


class IMemberScraper(ABC):
    """
    Service interface for scraping parliament members.
    """
    
    @abstractmethod
    def scrape_members(
        self,
        legislature: int,
        html_content: str = None
    ) -> List:
        """
        Scrape member list for a legislature.
        
        Args:
            legislature: Legislature number
            html_content: Optional pre-downloaded HTML
            
        Returns:
            List of member objects
        """
        pass
