"""
Cleaned text repository interface.

Defines contract for persisting cleaned minute text metadata.
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..entities import CleanedMinuteText


class ICleanedTextRepository(ABC):
    """
    Interface for managing cleaned text metadata persistence.
    
    Stores only metadata in database. Content is stored separately via
    IContentStorage (orchestrated by use case).
    """
    
    @abstractmethod
    def save_metadata(self, metadata: CleanedMinuteText) -> CleanedMinuteText:
        """
        Save cleaned text metadata to database.
        
        Args:
            metadata: CleanedMinuteText entity with all fields populated
            
        Returns:
            Saved CleanedMinuteText with id set
            
        Raises:
            ValueError: If metadata is invalid
        """
        pass
    
    @abstractmethod
    def find_by_minute_ref(
        self,
        minute_ref: str
    ) -> Optional[CleanedMinuteText]:
        """
        Find cleaned text metadata for a specific minute.
        
        Args:
            minute_ref: Minute reference
            
        Returns:
            CleanedMinuteText metadata if found, None otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, minute_ref: str) -> bool:
        """
        Check if cleaned text metadata exists for minute.
        
        Args:
            minute_ref: Minute reference
            
        Returns:
            True if metadata exists
        """
        pass
