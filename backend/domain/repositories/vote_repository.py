"""
Vote repository interface.

Defines contract for persisting vote data.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Vote, MemberVote


class IVoteRepository(ABC):
    """
    Interface for managing vote data persistence.
    
    Handles CRUD operations for votes and member vote records.
    """
    
    @abstractmethod
    def save_vote(self, vote: Vote) -> Vote:
        """
        Save a vote record.
        
        Args:
            vote: Vote entity to save
            
        Returns:
            Saved Vote with id set
            
        Raises:
            ValueError: If vote data is invalid
        """
        pass
    
    @abstractmethod
    def save_member_vote(self, member_vote: MemberVote) -> MemberVote:
        """
        Save a member vote record.
        
        Args:
            member_vote: MemberVote entity to save
            
        Returns:
            Saved MemberVote with id set
            
        Raises:
            ValueError: If member_vote data is invalid
        """
        pass
    
    @abstractmethod
    def save_vote_with_members(
        self,
        vote: Vote,
        member_votes: List[MemberVote]
    ) -> tuple[Vote, List[MemberVote]]:
        """
        Save a vote and all associated member votes in a transaction.
        
        More efficient and safer than separate calls.
        
        Args:
            vote: Vote entity to save
            member_votes: List of MemberVote entities to save
            
        Returns:
            Tuple of (saved Vote, list of saved MemberVotes) with ids set
            
        Raises:
            ValueError: If any data is invalid
        """
        pass
    
    @abstractmethod
    def find_votes_by_session(
        self,
        session_ref: str,
        legislature: Optional[int] = None
    ) -> List[Vote]:
        """
        Find all votes for a session.
        
        Args:
            session_ref: Session reference (CRIV format)
            legislature: Optional legislature filter
            
        Returns:
            List of Vote entities for the session
        """
        pass
    
    @abstractmethod
    def find_member_votes_by_vote(
        self,
        vote_id: int
    ) -> List[MemberVote]:
        """
        Find all member votes for a specific vote.
        
        Args:
            vote_id: Vote identifier
            
        Returns:
            List of MemberVote entities for the vote
        """
        pass
    
    @abstractmethod
    def find_member_votes_by_member(
        self,
        member_id: str,
        legislature: int
    ) -> List[MemberVote]:
        """
        Find all votes cast by a member.
        
        Args:
            member_id: Member identifier
            legislature: Legislature number
            
        Returns:
            List of MemberVote entities for the member
        """
        pass
    
    @abstractmethod
    def delete_votes_by_session(self, session_ref: str) -> int:
        """
        Delete all votes and member votes for a session.
        
        Useful for re-processing a session.
        
        Args:
            session_ref: Session reference (CRIV format)
            
        Returns:
            Number of vote records deleted
        """
        pass
