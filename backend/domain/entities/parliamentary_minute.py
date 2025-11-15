"""
Parliamentary Minute domain entity.

Represents a parliamentary session minute with its metadata and content reference.
"""

from dataclasses import dataclass
from typing import Optional

from .session_metadata import SessionMetadata


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
