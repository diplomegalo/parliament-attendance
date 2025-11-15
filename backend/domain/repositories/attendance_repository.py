"""
Attendance repository interface.

Defines contract for persisting attendance data.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import MemberPresence


class IAttendanceRepository(ABC):
    """
    Interface for managing attendance data persistence.
    
    Handles CRUD operations for member presence records.
    """
    
    @abstractmethod
    def save(self, presence: MemberPresence) -> MemberPresence:
        """
        Save a member presence record.
        
        Args:
            presence: MemberPresence entity to save
            
        Returns:
            Saved MemberPresence with id set
            
        Raises:
            ValueError: If presence data is invalid
        """
        pass
    
    @abstractmethod
    def save_batch(
        self,
        presences: List[MemberPresence]
    ) -> List[MemberPresence]:
        """
        Save multiple presence records in a batch.
        
        More efficient than multiple save() calls for bulk operations.
        
        Args:
            presences: List of MemberPresence entities to save
            
        Returns:
            List of saved MemberPresence entities with ids set
            
        Raises:
            ValueError: If any presence data is invalid
        """
        pass
    
    @abstractmethod
    def find_by_session(
        self,
        session_ref: str,
        legislature: Optional[int] = None
    ) -> List[MemberPresence]:
        """
        Find all attendance records for a session.
        
        Args:
            session_ref: Session reference (CRIV format)
            legislature: Optional legislature filter
            
        Returns:
            List of MemberPresence entities for the session
        """
        pass
    
    @abstractmethod
    def find_by_member(
        self,
        member_id: str,
        legislature: int
    ) -> List[MemberPresence]:
        """
        Find all attendance records for a member.
        
        Args:
            member_id: Member identifier
            legislature: Legislature number
            
        Returns:
            List of MemberPresence entities for the member
        """
        pass
    
    @abstractmethod
    def delete_by_session(self, session_ref: str) -> int:
        """
        Delete all attendance records for a session.
        
        Useful for re-processing a session.
        
        Args:
            session_ref: Session reference (CRIV format)
            
        Returns:
            Number of records deleted
        """
        pass
