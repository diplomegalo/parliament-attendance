"""
Vote parser repository interface.

Defines contract for AI-powered parsing of votes from minutes.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from ..entities import Vote, MemberVote


class IVoteParser(ABC):
    """
    Interface for parsing votes from parliamentary minute text.
    
    Implementations use AI (OpenAI, Claude, or local LLM) to extract
    vote information and member positions from cleaned minute text.
    """
    
    @abstractmethod
    def parse_votes(
        self,
        minute_text: str,
        session_ref: str,
        legislature: int
    ) -> List[Tuple[Vote, List[MemberVote]]]:
        """
        Parse vote information from minute text.
        
        Uses AI to identify votes and member positions during
        the parliamentary session.
        
        Args:
            minute_text: Cleaned text from parliamentary minute
            session_ref: Session reference (CRIV format)
            legislature: Legislature number
            
        Returns:
            List of tuples (Vote, List[MemberVote]) where each tuple
            contains a vote and all member votes for that vote
            
        Raises:
            ValueError: If minute_text is empty or invalid
            RuntimeError: If AI parsing fails
        """
        pass
