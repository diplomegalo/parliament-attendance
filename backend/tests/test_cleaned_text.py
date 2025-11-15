"""
Tests for CleanedMinuteText entity.

Tests cleaned text metadata storage and traceability.
"""

import unittest
from datetime import datetime
from domain.entities import CleanedMinuteText


class TestCleanedMinuteText(unittest.TestCase):
    """Test CleanedMinuteText entity."""
    
    def test_create_valid_metadata(self):
        """Test creating valid cleaned text metadata."""
        metadata = CleanedMinuteText(
            minute_ref="0001",
            content_storage_key="/path/to/cleaned/0001.txt",
            cleaning_method="html_strip_v1",
            text_hash="abc123" * 10,  # Simulate SHA-256 length
            created_at=datetime(2024, 1, 15, 10, 30)
        )
        
        self.assertEqual(metadata.minute_ref, "0001")
        self.assertEqual(
            metadata.content_storage_key,
            "/path/to/cleaned/0001.txt"
        )
        self.assertEqual(metadata.cleaning_method, "html_strip_v1")
        self.assertEqual(metadata.text_hash, "abc123" * 10)
        self.assertEqual(
            metadata.created_at,
            datetime(2024, 1, 15, 10, 30)
        )
        self.assertIsNone(metadata.id)
    
    def test_create_factory_method(self):
        """Test factory method with provided hash."""
        text_hash = CleanedMinuteText.compute_hash("Sample text")
        
        metadata = CleanedMinuteText.create(
            minute_ref="0001",
            content_storage_key="/path/to/cleaned/0001.txt",
            text_hash=text_hash,
            cleaning_method="html_strip_v1"
        )
        
        self.assertEqual(metadata.minute_ref, "0001")
        self.assertEqual(
            metadata.content_storage_key,
            "/path/to/cleaned/0001.txt"
        )
        self.assertEqual(metadata.cleaning_method, "html_strip_v1")
        self.assertEqual(metadata.text_hash, text_hash)
        self.assertIsNotNone(metadata.created_at)
        self.assertIsInstance(metadata.created_at, datetime)
    
    def test_compute_hash_is_deterministic(self):
        """Test that same text produces same hash."""
        text = "Same text content"
        
        hash1 = CleanedMinuteText.compute_hash(text)
        hash2 = CleanedMinuteText.compute_hash(text)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 length
    
    def test_compute_hash_differs_for_different_text(self):
        """Test that different text produces different hash."""
        hash1 = CleanedMinuteText.compute_hash("Text A")
        hash2 = CleanedMinuteText.compute_hash("Text B")
        
        self.assertNotEqual(hash1, hash2)
    
    def test_empty_minute_ref_raises_error(self):
        """Test that empty minute_ref raises ValueError."""
        with self.assertRaises(ValueError):
            CleanedMinuteText(
                minute_ref="",
                content_storage_key="/path",
                cleaning_method="v1",
                text_hash="abc" * 20,
                created_at=datetime.now()
            )
    
    def test_empty_storage_key_raises_error(self):
        """Test that empty content_storage_key raises ValueError."""
        with self.assertRaises(ValueError):
            CleanedMinuteText(
                minute_ref="0001",
                content_storage_key="",
                cleaning_method="v1",
                text_hash="abc" * 20,
                created_at=datetime.now()
            )
    
    def test_empty_cleaning_method_raises_error(self):
        """Test that empty cleaning_method raises ValueError."""
        with self.assertRaises(ValueError):
            CleanedMinuteText(
                minute_ref="0001",
                content_storage_key="/path",
                cleaning_method="",
                text_hash="abc" * 20,
                created_at=datetime.now()
            )
    
    def test_empty_text_hash_raises_error(self):
        """Test that empty text_hash raises ValueError."""
        with self.assertRaises(ValueError):
            CleanedMinuteText(
                minute_ref="0001",
                content_storage_key="/path",
                cleaning_method="v1",
                text_hash="",
                created_at=datetime.now()
            )


if __name__ == '__main__':
    unittest.main()
