"""
Tests for PostgreSQL cleaned text repository.

Tests storage of metadata in database (content handled by use case).
"""

import unittest
from unittest.mock import MagicMock, patch
from infrastructure.repositories.cleaned_text_repository import (
    PostgreSQLCleanedTextRepository
)
from domain.entities import CleanedMinuteText
from datetime import datetime


class TestPostgreSQLCleanedTextRepository(unittest.TestCase):
    """Test PostgreSQL cleaned text repository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repository = PostgreSQLCleanedTextRepository()
    
    @patch('infrastructure.repositories.cleaned_text_repository.psycopg2')
    def test_save_metadata_inserts_to_database(self, mock_psycopg2):
        """Test saving metadata to database."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        
        # Mock database response
        mock_cursor.fetchone.return_value = (
            1,  # id
            datetime(2024, 1, 15, 10, 30),  # created_at
            None  # updated_at
        )
        
        metadata = CleanedMinuteText.create(
            minute_ref="0001",
            content_storage_key="/data/cleaned/0001.txt",
            text_hash="abc123def456",
            cleaning_method="html_strip_v1"
        )
        
        # Act
        result = self.repository.save_metadata(metadata)
        
        # Assert
        self.assertEqual(result.id, 1)
        self.assertEqual(result.minute_ref, "0001")
        self.assertEqual(
            result.content_storage_key,
            "/data/cleaned/0001.txt"
        )
        mock_cursor.execute.assert_called_once()
        
    @patch('infrastructure.repositories.cleaned_text_repository.psycopg2')
    def test_find_by_minute_ref_returns_metadata(self, mock_psycopg2):
        """Test finding metadata by minute reference."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        
        # Mock database row
        mock_cursor.fetchone.return_value = (
            1,  # id
            "0001",  # minute_ref
            "/data/cleaned/0001.txt",  # content_storage_key
            "html_strip_v1",  # cleaning_method
            "abc123",  # text_hash
            datetime(2024, 1, 15, 10, 30),  # created_at
            None  # updated_at
        )
        
        # Act
        result = self.repository.find_by_minute_ref("0001")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.minute_ref, "0001")
        self.assertEqual(result.content_storage_key, "/data/cleaned/0001.txt")
        self.assertEqual(result.cleaning_method, "html_strip_v1")
    
    @patch('infrastructure.repositories.cleaned_text_repository.psycopg2')
    def test_find_by_minute_ref_returns_none_when_not_found(
        self,
        mock_psycopg2
    ):
        """Test finding non-existent minute returns None."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = None
        
        # Act
        result = self.repository.find_by_minute_ref("9999")
        
        # Assert
        self.assertIsNone(result)
    
    @patch('infrastructure.repositories.cleaned_text_repository.psycopg2')
    def test_exists_returns_true_when_found(self, mock_psycopg2):
        """Test exists check when metadata is present."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = (1,)  # COUNT result
        
        # Act
        result = self.repository.exists("0001")
        
        # Assert
        self.assertTrue(result)
    
    @patch('infrastructure.repositories.cleaned_text_repository.psycopg2')
    def test_exists_returns_false_when_not_found(self, mock_psycopg2):
        """Test exists check for non-existent minute."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = (0,)  # COUNT result
        
        # Act
        result = self.repository.exists("9999")
        
        # Assert
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
