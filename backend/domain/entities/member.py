"""
Member domain entity.

Represents a parliament member during a specific legislature.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Member:
    """
    Domain entity representing a parliament member.
    
    A member serves during a specific legislature term.
    The same person can be a member across multiple legislatures,
    distinguished by the (member_id, legislature) composite key.
    
    Attributes:
        member_id: Unique identifier for the person
        legislature: Legislature number they serve in
        full_name: Complete official name
        last_name: Family name
        first_name: Given name
        id: Database ID (optional, set after persistence)
    """
    member_id: str
    legislature: int
    full_name: str
    last_name: str
    first_name: str
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate member data."""
        if not self.member_id or not self.member_id.strip():
            raise ValueError("Member ID cannot be empty")
        
        if self.legislature < 1:
            raise ValueError("Legislature must be positive")
        
        if not self.full_name or not self.full_name.strip():
            raise ValueError("Full name cannot be empty")
        
        if not self.last_name or not self.last_name.strip():
            raise ValueError("Last name cannot be empty")
        
        if not self.first_name or not self.first_name.strip():
            raise ValueError("First name cannot be empty")
    
    def get_display_name(self) -> str:
        """
        Get formatted display name.
        
        Returns:
            Formatted name (Last, First)
        """
        return f"{self.last_name}, {self.first_name}"
