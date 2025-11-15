"""
Parliamentary Session domain entity.

Represents a parliamentary session with its core business attributes.
This is a domain entity following DDD principles.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SessionReference:
    """Value object representing a session reference identifier."""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Session reference cannot be empty")
    
    def __str__(self) -> str:
        return self.value


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
    
    def __post_init__(self):
        if not self.description:
            raise ValueError("Session description cannot be empty")
        if not self.document_url:
            raise ValueError("Document URL cannot be empty")


@dataclass
class ParliamentaryMinute:
    """
    Domain entity representing a parliamentary session minute.
    
    This entity contains the storage reference to the full text content
    of a parliamentary session along with its metadata. Follows DDD aggregate
    root pattern.
    """
    metadata: SessionMetadata
    content_storage_key: str
    id: Optional[int] = None
    
    def __post_init__(self):
        if not self.content_storage_key:
            raise ValueError("Content storage key cannot be empty")
    
    def get_reference(self) -> str:
        """Get the session reference as string."""
        return str(self.metadata.reference)
    
    def is_provisional(self) -> bool:
        """Check if this minute is provisional (can be updated)."""
        return self.metadata.is_provisional
    
    def is_definitive(self) -> bool:
        """Check if this minute is definitive (immutable)."""
        return not self.metadata.is_provisional
