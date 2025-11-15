"""
Cleaned Minute Text domain entity.

Represents cleaned text extracted from parliamentary minutes for AI processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib


@dataclass
class CleanedMinuteText:
    """
    Domain entity representing cleaned text metadata.
    
    Stores metadata about preprocessed text for LLM consumption.
    Actual cleaned text is stored in content storage (file/blob).
    This enables reproducibility, debugging, and versioning of AI inputs.
    
    Attributes:
        minute_ref: Reference to the minute
        content_storage_key: Path/key to retrieve cleaned text from storage
        cleaning_method: Method/version used for cleaning
                        (e.g., "html_strip_v1")
        text_hash: SHA-256 hash of cleaned text for change detection
        created_at: Timestamp when metadata was created
        updated_at: Timestamp when metadata was last updated
        id: Database ID (optional, set after persistence)
    """
    minute_ref: str
    content_storage_key: str
    cleaning_method: str
    text_hash: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate cleaned text metadata."""
        if not self.minute_ref or not self.minute_ref.strip():
            raise ValueError("Minute reference cannot be empty")
        
        if (not self.content_storage_key or
                not self.content_storage_key.strip()):
            raise ValueError("Content storage key cannot be empty")
        
        if not self.cleaning_method or not self.cleaning_method.strip():
            raise ValueError("Cleaning method cannot be empty")
        
        if not self.text_hash or not self.text_hash.strip():
            raise ValueError("Text hash cannot be empty")
    
    @classmethod
    def create(
        cls,
        minute_ref: str,
        content_storage_key: str,
        text_hash: str,
        cleaning_method: str
    ) -> 'CleanedMinuteText':
        """
        Create a new CleanedMinuteText metadata record.
        
        Args:
            minute_ref: Reference to the minute
            content_storage_key: Path/key where cleaned text is stored
            text_hash: SHA-256 hash of cleaned text
            cleaning_method: Method used for cleaning
            
        Returns:
            New CleanedMinuteText instance
        """
        return cls(
            minute_ref=minute_ref,
            content_storage_key=content_storage_key,
            cleaning_method=cleaning_method,
            text_hash=text_hash,
            created_at=datetime.utcnow()
        )
    
    @staticmethod
    def compute_hash(text: str) -> str:
        """
        Compute SHA-256 hash of text.
        
        Args:
            text: Text to hash
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def has_changed(self, new_text: str) -> bool:
        """
        Check if new text differs from stored text.
        
        Args:
            new_text: New cleaned text to compare
            
        Returns:
            True if text has changed
        """
        new_hash = hashlib.sha256(new_text.encode('utf-8')).hexdigest()
        return new_hash != self.text_hash
