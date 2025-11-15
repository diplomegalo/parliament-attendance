"""
Minute Content Retriever interface.

Defines how to fetch full text content from external sources.
"""

from abc import ABC, abstractmethod


class IMinuteContentRetriever(ABC):
    """
    Service interface for retrieving minute content.
    
    This port defines how to fetch the full text content of a minute
    from external sources (e.g., web scraping).
    """
    
    @abstractmethod
    def retrieve_content(self, document_url: str) -> str:
        """
        Retrieve the full text content from a document URL.
        
        Args:
            document_url: URL to the minute document
            
        Returns:
            Full text content of the minute
        """
        pass
