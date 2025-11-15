"""
Vote Position value object.

Represents a member's position on a parliamentary vote.
"""

from enum import Enum


class VotePosition(Enum):
    """
    Member position on a vote.
    
    Represents the three possible voting positions in parliamentary procedure.
    """
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    
    def __str__(self) -> str:
        return self.value
