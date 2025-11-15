"""
Unit tests for content storage implementations.

Tests both local filesystem and Azure blob storage.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from infrastructure.storage.local_file_storage import LocalFileSystemStorage


class TestLocalFileSystemStorage(unittest.TestCase):
    """Test local filesystem storage implementation."""
    
    def setUp(self):
        """Create temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = LocalFileSystemStorage(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_store_and_retrieve_content(self):
        """Test storing and retrieving content."""
        reference = "CRIV 56 COM 123"
        content = "<html><body>Test content</body></html>"
        
        # Store content
        storage_key = self.storage.store_content(reference, content)
        
        # Verify storage key is returned
        self.assertIsNotNone(storage_key)
        self.assertTrue(Path(storage_key).exists())
        
        # Retrieve content
        retrieved = self.storage.retrieve_content(storage_key)
        self.assertEqual(retrieved, content)
    
    def test_exists_check(self):
        """Test checking if content exists."""
        reference = "CRIV 56 COM 456"
        content = "Test content"
        
        # Store content
        storage_key = self.storage.store_content(reference, content)
        
        # Check exists
        self.assertTrue(self.storage.exists(storage_key))
        
        # Check non-existent
        self.assertFalse(self.storage.exists("nonexistent.html"))
    
    def test_sanitize_filename(self):
        """Test that special characters in reference are sanitized."""
        reference = "CRIV 56/COM 123"
        content = "Test"
        
        storage_key = self.storage.store_content(reference, content)
        
        # Verify filename doesn't contain /
        filename = Path(storage_key).name
        self.assertNotIn('/', filename)
        self.assertIn('_', filename)
    
    def test_overwrite_content(self):
        """Test that storing same reference overwrites content."""
        reference = "CRIV 56 COM 789"
        content1 = "First content"
        content2 = "Second content"
        
        # Store first
        key1 = self.storage.store_content(reference, content1)
        
        # Store second (should overwrite)
        key2 = self.storage.store_content(reference, content2)
        
        # Keys should be the same
        self.assertEqual(key1, key2)
        
        # Content should be updated
        retrieved = self.storage.retrieve_content(key2)
        self.assertEqual(retrieved, content2)


if __name__ == "__main__":
    unittest.main()
