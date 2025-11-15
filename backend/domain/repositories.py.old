"""
Repository interfaces (ports) for the domain layer.

These are abstract interfaces that define how the domain interacts with
external systems. Implementations belong in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List, Set
from .entities import ParliamentaryMinute, SessionMetadata


class ISessionMetadataRepository(ABC):
    """
    Repository interface for retrieving session metadata.
    
    This port defines how to fetch session information from external sources
    without coupling to specific implementation details.
    """
    
    @abstractmethod
    def retrieve_all_sessions(self) -> List[SessionMetadata]:
        """
        Retrieve metadata for all available parliamentary sessions.
        
        Returns:
            List of SessionMetadata objects
        """
        pass


class IMinuteRepository(ABC):
    """
    Repository interface for parliamentary minutes.
    
    Defines operations for storing and retrieving minutes without
    coupling to database implementation details.
    """
    
    @abstractmethod
    def save_minutes(self, minutes: List[ParliamentaryMinute]) -> None:
        """
        Save multiple minutes to persistent storage.
        
        Args:
            minutes: List of ParliamentaryMinute entities to save
        """
        pass
    
    @abstractmethod
    def find_existing_references(self, references: List[str]) -> Set[str]:
        """
        Find which session references already exist in storage.
        
        Args:
            references: List of session reference strings to check
            
        Returns:
            Set of reference strings that exist in storage
        """
        pass


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


class IContentStorage(ABC):
    """
    Service interface for storing and retrieving large content files.
    
    This port defines how to store raw content (HTML, text) separately
    from database metadata, delegating to appropriate storage infrastructure
    (filesystem, blob storage, etc.).
    """
    
    @abstractmethod
    def store_content(self, reference: str, content: str) -> str:
        """
        Store content and return a storage key/path.
        
        Args:
            reference: Unique reference identifier for the content
            content: The full text content to store
            
        Returns:
            Storage key/path that can be used to retrieve the content
        """
        pass
    
    @abstractmethod
    def retrieve_content(self, storage_key: str) -> str:
        """
        Retrieve content using its storage key.
        
        Args:
            storage_key: The key/path returned by store_content
            
        Returns:
            The stored content
        """
        pass
    
    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """
        Check if content exists at the given storage key.
        
        Args:
            storage_key: The key/path to check
            
        Returns:
            True if content exists, False otherwise
        """
        pass


class IMemberRepository(ABC):
    """
    Repository interface for parliament members.
    
    Defines operations for storing and checking member data.
    """
    
    @abstractmethod
    def has_members_for_legislature(self, legislature: int) -> bool:
        """
        Check if members exist for a specific legislature.
        
        Args:
            legislature: Legislature number to check
            
        Returns:
            True if members exist, False otherwise
        """
        pass
    
    @abstractmethod
    def save_members(self, members: List) -> None:
        """
        Save multiple members to persistent storage.
        
        Args:
            members: List of member entities to save
        """
        pass
    
    @abstractmethod
    def count_members_for_legislature(self, legislature: int) -> int:
        """
        Count members for a specific legislature.
        
        Args:
            legislature: Legislature number
            
        Returns:
            Number of members
        """
        pass


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
