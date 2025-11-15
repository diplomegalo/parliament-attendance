"""
Legislature value object.

Represents a legislative period/term number.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Legislature:
    """
    Value object representing a legislative period.
    
    A legislature is a fixed-term period during which a parliament operates.
    Belgian parliament uses sequential numbers (e.g., 55, 56, 57).
    """
    number: int
    
    def __post_init__(self):
        if self.number < 1:
            raise ValueError(
                f"Legislature number must be positive, got {self.number}"
            )
    
    def __str__(self) -> str:
        return str(self.number)
    
    def __int__(self) -> int:
        return self.number
