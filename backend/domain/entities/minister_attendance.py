"""
Minister Attendance domain entity.

Represents a minister's attendance in a specific parliamentary session.
Only tracks attendance for sessions with at least one vote nominatif.
"""

from dataclasses import dataclass
from typing import Optional
from ..value_objects import ConfidenceScore


@dataclass
class MinisterAttendance:
    """
    Domain entity representing minister attendance in a session.
    
    Tracks whether a minister was present in sessions containing vote
    nominatif. Sessions without vote nominatif are excluded from
    attendance tracking. AI-powered extraction provides confidence scores.
    
    Attributes:
        minister_id: Minister identifier (from members table)
        minute_ref: Minute reference (links to minutes table)
        legislature: Legislature number
        present: Whether the minister was present (name in attendance)
        confidence_score: AI confidence (None or ConfidenceScore)
        context: Optional context (e.g., "Vote 3")
        id: Database ID (optional, set after persistence)
    """
    minister_id: str
    minute_ref: str
    legislature: int
    present: bool
    confidence_score: Optional[ConfidenceScore] = None
    context: Optional[str] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate minister attendance data."""
        if not self.minister_id or not self.minister_id.strip():
            raise ValueError("Minister ID cannot be empty")
        
        if not self.minute_ref or not self.minute_ref.strip():
            raise ValueError("Minute reference cannot be empty")
        
        if self.legislature <= 0:
            raise ValueError("Legislature must be positive")
        
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
