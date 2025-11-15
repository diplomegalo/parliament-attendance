"""
Vote domain entity.

Represents a parliamentary vote event.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Vote:
    """
    Domain entity representing a parliamentary vote.
    
    A vote happens during a session on a specific topic or bill.
    Multiple members cast individual votes on this topic.
    
    Legislature is obtained via session_ref -> minutes table relationship,
    eliminating duplication.
    
    Attributes:
        session_ref: Session where vote occurred (links to minutes table)
        vote_topic: Topic/bill being voted on
        vote_date: Date of the vote
        id: Database ID (optional, set after persistence)
    """
    session_ref: str
    vote_topic: str
    vote_date: date
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate vote data."""
        if not self.session_ref or not self.session_ref.strip():
            raise ValueError("Session reference cannot be empty")
        
        if not self.vote_topic or not self.vote_topic.strip():
            raise ValueError("Vote topic cannot be empty")
