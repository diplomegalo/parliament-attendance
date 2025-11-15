"""
Unit tests for domain entities.

Tests the pure domain logic without external dependencies.
"""

import unittest
from datetime import datetime

from domain.entities import (
    SessionReference,
    SessionMetadata,
    ParliamentaryMinute
)


class TestSessionReference(unittest.TestCase):
    """Test SessionReference value object."""
    
    def test_valid_reference(self):
        """Test creating a valid session reference."""
        ref = SessionReference("CRIV 56 COM 123")
        self.assertEqual(str(ref), "CRIV 56 COM 123")
    
    def test_empty_reference_raises_error(self):
        """Test that empty reference raises ValueError."""
        with self.assertRaises(ValueError):
            SessionReference("")
    
    def test_whitespace_reference_raises_error(self):
        """Test that whitespace-only reference raises ValueError."""
        with self.assertRaises(ValueError):
            SessionReference("   ")


class TestSessionMetadata(unittest.TestCase):
    """Test SessionMetadata value object."""
    
    def test_valid_metadata(self):
        """Test creating valid session metadata."""
        ref = SessionReference("CRIV 56 COM 123")
        date = datetime(2024, 11, 14)
        
        metadata = SessionMetadata(
            reference=ref,
            date=date,
            description="Séance plénière",
            document_url="/path/to/doc",
            is_provisional=True,
            legislature=56
        )
        
        self.assertEqual(metadata.reference, ref)
        self.assertEqual(metadata.date, date)
        self.assertEqual(metadata.description, "Séance plénière")
        self.assertTrue(metadata.is_provisional)
    
    def test_empty_description_raises_error(self):
        """Test that empty description raises ValueError."""
        ref = SessionReference("CRIV 56 COM 123")
        
        with self.assertRaises(ValueError):
            SessionMetadata(
                reference=ref,
                date=datetime(2024, 11, 14),
                description="",
                document_url="/path",
                is_provisional=True,
                legislature=56
            )
    
    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        ref = SessionReference("CRIV 56 COM 123")
        
        with self.assertRaises(ValueError):
            SessionMetadata(
                reference=ref,
                date=datetime(2024, 11, 14),
                description="Session",
                document_url="",
                is_provisional=True,
                legislature=56
            )
    
    def test_invalid_legislature_raises_error(self):
        """Test that invalid legislature raises ValueError."""
        ref = SessionReference("CRIV 56 COM 123")
        
        with self.assertRaises(ValueError) as context:
            SessionMetadata(
                reference=ref,
                date=datetime(2024, 11, 14),
                description="Session",
                document_url="/path",
                is_provisional=True,
                legislature=0
            )
        
        self.assertIn(
            "Legislature must be a positive integer",
            str(context.exception)
        )


class TestParliamentaryMinute(unittest.TestCase):
    """Test ParliamentaryMinute entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = SessionMetadata(
            reference=SessionReference("CRIV 56 COM 123"),
            date=datetime(2024, 11, 14),
            description="Séance plénière",
            document_url="/path/to/doc",
            is_provisional=True,
            legislature=56
        )
    
    def test_valid_minute(self):
        """Test creating a valid parliamentary minute."""
        minute = ParliamentaryMinute(
            metadata=self.metadata,
            content_storage_key="data/minutes/CRIV_56_COM_123.html"
        )
        
        self.assertEqual(minute.metadata, self.metadata)
        self.assertEqual(minute.get_reference(), "CRIV 56 COM 123")
        self.assertTrue(minute.is_provisional())
        self.assertFalse(minute.is_definitive())
        self.assertIsNone(minute.id)
    
    def test_minute_with_id(self):
        """Test minute with database ID."""
        minute = ParliamentaryMinute(
            metadata=self.metadata,
            content_storage_key="storage_key",
            id=42
        )
        
        self.assertEqual(minute.id, 42)
    
    def test_empty_storage_key_raises_error(self):
        """Test that empty storage key raises ValueError."""
        with self.assertRaises(ValueError):
            ParliamentaryMinute(
                metadata=self.metadata,
                content_storage_key=""
            )
    
    def test_definitive_minute(self):
        """Test definitive minute logic."""
        metadata = SessionMetadata(
            reference=SessionReference("CRIV 56 COM 456"),
            date=datetime(2024, 11, 14),
            description="Séance",
            document_url="/path",
            is_provisional=False,
            legislature=56
        )
        
        minute = ParliamentaryMinute(
            metadata=metadata,
            content_storage_key="storage_key"
        )
        
        self.assertFalse(minute.is_provisional())
        self.assertTrue(minute.is_definitive())


if __name__ == "__main__":
    unittest.main()
