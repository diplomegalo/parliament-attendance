"""
Parliamentary minute data model.

This module contains the Minute class that represents a parliamentary
meeting record with all its attributes.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Minister:
    """Represents a government minister."""
    name: str

    def __repr__(self) -> str:
        return f"Minister(name='{self.name}')"


class Minute:
    """Represents a parliamentary minute (meeting record)."""

    def __init__(
        self,
        id: Optional[int] = None,
        ref: str = "",
        date: str = "",
        session: str = "",
        url: str = "",
        is_temporary: bool = False,
        text_integral: str = ""
    ):
        """
        Initialize a Minute object.

        Args:
            id: Database ID (optional, auto-generated)
            ref: Reference identifier for the minute
            date: Date of the parliamentary session
            session: Session description/name
            url: URL to the full document
            is_temporary: Whether this is a temporary/provisional version
            text_integral: Full text content of the minute
        """
        self.id = id
        self.ref = ref
        self.date = date
        self.session = session
        self.url = url
        self.is_temporary = is_temporary
        self.text_integral = text_integral

    def __repr__(self) -> str:
        """String representation for debugging."""
        text_preview = (
            self.text_integral[:100] + "..."
            if len(self.text_integral) > 100
            else self.text_integral
        )
        return (
            f"Minute(id={self.id}, ref='{self.ref}', date='{self.date}', "
            f"session='{self.session}', url='{self.url}', "
            f"is_temporary={self.is_temporary}, "
            f"text_integral='{text_preview}')"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Minute {self.ref} - {self.date} ({self.session})"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'ref': self.ref,
            'date': self.date,
            'session': self.session,
            'url': self.url,
            'is_temporary': self.is_temporary,
            'text_integral': self.text_integral
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Minute':
        """Create Minute from dictionary."""
        return cls(
            id=data.get('id'),
            ref=data.get('ref', ''),
            date=data.get('date', ''),
            session=data.get('session', ''),
            url=data.get('url', ''),
            is_temporary=data.get('is_temporary', False),
            text_integral=data.get('text_integral', '')
        )
