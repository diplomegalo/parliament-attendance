"""
Content Storage interface.

Defines how to store and retrieve large content files.
"""

from abc import ABC, abstractmethod


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
