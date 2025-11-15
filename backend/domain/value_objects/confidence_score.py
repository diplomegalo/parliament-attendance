"""
Confidence Score value object.

Represents AI/ML confidence level for extracted data.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceScore:
    """
    Value object representing confidence level (0.0 to 1.0).
    
    Used to track AI extraction confidence for attendance and voting data.
    Higher values indicate more reliable extractions.
    """
    value: float
    
    def __post_init__(self):
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(
                f"Confidence score must be between 0.0 and 1.0, "
                f"got {self.value}"
            )
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """
        Check if confidence meets a threshold.
        
        Args:
            threshold: Minimum confidence level (default 0.7)
            
        Returns:
            True if confidence >= threshold
        """
        return self.value >= threshold
    
    def __float__(self) -> float:
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value:.2%}"
