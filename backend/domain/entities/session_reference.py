"""
Session Reference value object.

Represents a unique identifier for a parliamentary session.
"""

from dataclasses import dataclass


@dataclass
class SessionReference:
    """Value object representing a session reference identifier."""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Session reference cannot be empty")
    
    def __str__(self) -> str:
        return self.value
