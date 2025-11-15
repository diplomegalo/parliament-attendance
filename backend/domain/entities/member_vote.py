"""
Member Vote domain entity.

Represents an individual member's position on a parliamentary vote.
"""

from dataclasses import dataclass
from typing import Optional
from ..value_objects import VotePosition, ConfidenceScore


@dataclass
class MemberVote:
    """
    Domain entity representing a member's vote on a specific topic.
    
    Links a member to a vote with their position (yes, no, abstain).
    AI extraction provides confidence scores.
    
    Legislature is obtained via vote_id -> votes -> session_ref -> minutes,
    eliminating duplication.
    
    Attributes:
        vote_id: Reference to Vote entity
        member_id: Member identifier
        position: Vote position (VotePosition enum)
        confidence_score: AI confidence in detection (None or ConfidenceScore)
        id: Database ID (optional, set after persistence)
    """
    vote_id: int
    member_id: str
    position: VotePosition
    confidence_score: Optional[ConfidenceScore] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate member vote data."""
        if not self.member_id or not self.member_id.strip():
            raise ValueError("Member ID cannot be empty")
        
        if self.vote_id < 1:
            raise ValueError("Vote ID must be positive")
        
        if not isinstance(self.position, VotePosition):
            raise ValueError(
                f"Position must be VotePosition enum, got {type(self.position)}"
            )
        
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
