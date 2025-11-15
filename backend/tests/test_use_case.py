"""
Unit tests for the synchronization use case.

Tests business logic in isolation using mock repositories.
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from application.use_cases import SynchronizeMinutesUseCase
from domain.entities import SessionMetadata, SessionReference, ParliamentaryMinute


class TestSynchronizeMinutesUseCase(unittest.TestCase):
    """Test the SynchronizeMinutesUseCase business logic."""
    
    def setUp(self):
        """Set up test fixtures with mock dependencies."""
        self.session_repo = Mock()
        self.minute_repo = Mock()
        self.content_retriever = Mock()
        self.content_storage = Mock()
        
        self.use_case = SynchronizeMinutesUseCase(
            session_metadata_repo=self.session_repo,
            minute_repo=self.minute_repo,
            content_retriever=self.content_retriever,
            content_storage=self.content_storage
        )
    
    def test_execute_with_no_sessions(self):
        """Test execution when no sessions are available."""
        self.session_repo.retrieve_all_sessions.return_value = []
        
        self.use_case.execute()
        
        # Should not call save or retrieve content
        self.content_retriever.retrieve_content.assert_not_called()
        self.minute_repo.save_minutes.assert_not_called()
    
    def test_execute_with_only_provisional_sessions(self):
        """Test execution with only provisional sessions."""
        # Setup mock data
        provisional_metadata = SessionMetadata(
            reference=SessionReference("PROV001"),
            date=datetime(2024, 11, 14),
            description="Provisional session",
            document_url="/prov001",
            is_provisional=True
        )
        
        self.session_repo.retrieve_all_sessions.return_value = [provisional_metadata]
        self.content_retriever.retrieve_content.return_value = "<html>Content</html>"
        self.content_storage.store_content.return_value = "storage/PROV001.html"
        
        # Execute
        self.use_case.execute()
        
        # Verify
        self.content_retriever.retrieve_content.assert_called_once_with("/prov001")
        self.minute_repo.save_minutes.assert_called_once()
        
        saved_minutes = self.minute_repo.save_minutes.call_args[0][0]
        self.assertEqual(len(saved_minutes), 1)
        self.assertTrue(saved_minutes[0].is_provisional())
    
    def test_execute_filters_existing_definitive_sessions(self):
        """Test that existing definitive sessions are not processed."""
        # Setup sessions
        definitive1 = SessionMetadata(
            reference=SessionReference("DEF001"),
            date=datetime(2024, 11, 14),
            description="Definitive session 1",
            document_url="/def001",
            is_provisional=False
        )
        
        definitive2 = SessionMetadata(
            reference=SessionReference("DEF002"),
            date=datetime(2024, 11, 15),
            description="Definitive session 2",
            document_url="/def002",
            is_provisional=False
        )
        
        self.session_repo.retrieve_all_sessions.return_value = [definitive1, definitive2]
        
        # DEF001 exists, DEF002 doesn't
        self.minute_repo.find_existing_references.return_value = {"DEF001"}
        self.content_retriever.retrieve_content.return_value = "<html>Content</html>"
        self.content_storage.store_content.return_value = "storage/DEF002.html"
        
        # Execute
        self.use_case.execute()
        
        # Verify only DEF002 is processed
        self.content_retriever.retrieve_content.assert_called_once_with("/def002")
        saved_minutes = self.minute_repo.save_minutes.call_args[0][0]
        self.assertEqual(len(saved_minutes), 1)
        self.assertEqual(saved_minutes[0].get_reference(), "DEF002")
    
    def test_execute_processes_all_provisional_and_new_definitive(self):
        """Test that provisional sessions are always processed with new definitive."""
        # Setup mixed sessions
        provisional = SessionMetadata(
            reference=SessionReference("PROV001"),
            date=datetime(2024, 11, 14),
            description="Provisional",
            document_url="/prov001",
            is_provisional=True
        )
        
        existing_def = SessionMetadata(
            reference=SessionReference("DEF001"),
            date=datetime(2024, 11, 15),
            description="Existing definitive",
            document_url="/def001",
            is_provisional=False
        )
        
        new_def = SessionMetadata(
            reference=SessionReference("DEF002"),
            date=datetime(2024, 11, 16),
            description="New definitive",
            document_url="/def002",
            is_provisional=False
        )
        
        self.session_repo.retrieve_all_sessions.return_value = [
            provisional, existing_def, new_def
        ]
        
        self.minute_repo.find_existing_references.return_value = {"DEF001"}
        self.content_retriever.retrieve_content.return_value = (
            "<html>Content</html>"
        )
        self.content_storage.store_content.return_value = "storage/key.html"
        
        # Execute
        self.use_case.execute()
        
        # Verify provisional + new definitive are processed
        self.assertEqual(self.content_retriever.retrieve_content.call_count, 2)
        saved_minutes = self.minute_repo.save_minutes.call_args[0][0]
        self.assertEqual(len(saved_minutes), 2)
        
        refs = {m.get_reference() for m in saved_minutes}
        self.assertEqual(refs, {"PROV001", "DEF002"})
    
    def test_execute_handles_content_retrieval_failure(self):
        """Test that failures in content retrieval don't stop processing."""
        session1 = SessionMetadata(
            reference=SessionReference("S001"),
            date=datetime(2024, 11, 14),
            description="Session 1",
            document_url="/s001",
            is_provisional=True
        )
        
        session2 = SessionMetadata(
            reference=SessionReference("S002"),
            date=datetime(2024, 11, 15),
            description="Session 2",
            document_url="/s002",
            is_provisional=True
        )
        
        self.session_repo.retrieve_all_sessions.return_value = [session1, session2]
        
        # First call fails, second succeeds
        self.content_retriever.retrieve_content.side_effect = [
            Exception("Network error"),
            "<html>Content</html>"
        ]
        self.content_storage.store_content.return_value = "storage/S002.html"
        
        # Execute
        self.use_case.execute()
        
        # Verify second session is still saved
        saved_minutes = self.minute_repo.save_minutes.call_args[0][0]
        self.assertEqual(len(saved_minutes), 1)
        self.assertEqual(saved_minutes[0].get_reference(), "S002")


if __name__ == "__main__":
    unittest.main()
