"""
Member Presence domain entity.

Represents a member's presence in a specific parliamentary session.
"""

from dataclasses import dataclass
from typing import Optional
from ..value_objects import ConfidenceScore


@dataclass
class MemberPresence:
    """
    Domain entity representing member attendance in a session.
    
    Tracks whether a member was present and spoke during a session.
    AI-powered extraction provides confidence scores for accuracy.
    
    Legislature is obtained via session_ref -> minutes table relationship,
    eliminating duplication.
    
    Attributes:
        member_id: Member identifier (from members table)
        session_ref: Session reference (links to minutes table)
        spoke: Whether the member spoke during the session
        interventions_count: Number of times member spoke
        confidence_score: AI confidence in detection (None or ConfidenceScore)
        id: Database ID (optional, set after persistence)
    """
    member_id: str
    session_ref: str
    spoke: bool = False
    interventions_count: int = 0
    confidence_score: Optional[ConfidenceScore] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate presence data."""
        if not self.member_id or not self.member_id.strip():
            raise ValueError("Member ID cannot be empty")
        
        if not self.session_ref or not self.session_ref.strip():
            raise ValueError("Session reference cannot be empty")
        
        if self.interventions_count < 0:
            raise ValueError("Interventions count cannot be negative")
        
        # Convert float to ConfidenceScore if needed
        if isinstance(self.confidence_score, float):
            object.__setattr__(
                self,
                'confidence_score',
                ConfidenceScore(self.confidence_score)
            )
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """
        Check if detection confidence meets threshold.
        
        Args:
            threshold: Minimum confidence (default 0.7)
            
        Returns:
            True if confidence >= threshold
        """
        if self.confidence_score is None:
            return False
        return self.confidence_score.is_confident(threshold)
