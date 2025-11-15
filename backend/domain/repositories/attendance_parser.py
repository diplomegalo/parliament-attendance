"""
Attendance parser repository interface.

Defines contract for AI-powered parsing of attendance from minutes.
"""

from abc import ABC, abstractmethod
from typing import List
from ..entities import MemberPresence


class IAttendanceParser(ABC):
    """
    Interface for parsing attendance from parliamentary minute text.
    
    Implementations use AI (OpenAI, Claude, or local LLM) to extract
    member presence and speaking information from cleaned minute text.
    """
    
    @abstractmethod
    def parse_attendance(
        self,
        minute_text: str,
        session_ref: str,
        legislature: int
    ) -> List[MemberPresence]:
        """
        Parse attendance information from minute text.
        
        Uses AI to identify which members were present and spoke
        during the parliamentary session.
        
        Args:
            minute_text: Cleaned text from parliamentary minute
            session_ref: Session reference (CRIV format)
            legislature: Legislature number
            
        Returns:
            List of MemberPresence entities with confidence scores
            
        Raises:
            ValueError: If minute_text is empty or invalid
            RuntimeError: If AI parsing fails
        """
        pass
