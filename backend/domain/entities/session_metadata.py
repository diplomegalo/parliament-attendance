"""
Session Metadata value object.

Contains the core identifying information for a parliamentary session.
"""

from dataclasses import dataclass
from datetime import datetime

from .session_reference import SessionReference


@dataclass
class SessionMetadata:
    """
    Value object containing session metadata.
    
    Immutable object representing the core identifying information
    for a parliamentary session.
    """
    reference: SessionReference
    date: datetime
    description: str
    document_url: str
    is_provisional: bool
    legislature: int
    
    def __post_init__(self):
        if not self.description:
            raise ValueError("Session description cannot be empty")
        if not self.document_url:
            raise ValueError("Document URL cannot be empty")
        if self.legislature < 1:
            raise ValueError("Legislature must be a positive integer")
