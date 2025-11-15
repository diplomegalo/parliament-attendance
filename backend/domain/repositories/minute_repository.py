"""
Minute Repository interface.

Defines operations for storing and retrieving parliamentary minutes.
"""

from abc import ABC, abstractmethod
from typing import List, Set

from domain.entities.parliamentary_minute import ParliamentaryMinute


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
    
    @abstractmethod
    def find_by_legislature(
        self, legislature: int
    ) -> List[ParliamentaryMinute]:
        """
        Find all minutes for a specific legislature.
        
        Args:
            legislature: Legislature number
            
        Returns:
            List of ParliamentaryMinute entities
        """
        pass
