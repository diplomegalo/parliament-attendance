"""
Member Repository interface.

Defines operations for storing and checking parliament member data.
"""

from abc import ABC, abstractmethod
from typing import List


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
    
    @abstractmethod
    def find_by_legislature(self, legislature: int) -> List:
        """
        Find all members for a specific legislature.
        
        Args:
            legislature: Legislature number
            
        Returns:
            List of member entities
        """
        pass
