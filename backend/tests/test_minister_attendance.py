"""
Tests for minister attendance functionality.

Tests the minister attendance domain entity, repository, and parser.
"""

import pytest
from domain.entities.minister_attendance import MinisterAttendance
from domain.value_objects import ConfidenceScore


class TestMinisterAttendanceEntity:
    """Test MinisterAttendance domain entity."""
    
    def test_create_minister_attendance(self):
        """Test creating a valid minister attendance record."""
        attendance = MinisterAttendance(
            minister_id="07683",
            minute_ref="0072",
            legislature=56,
            present=True,
            confidence_score=ConfidenceScore(0.95),
            context="Vote 3"
        )
        
        assert attendance.minister_id == "07683"
        assert attendance.minute_ref == "0072"
        assert attendance.legislature == 56
        assert attendance.present is True
        assert attendance.confidence_score.value == 0.95
        assert attendance.context == "Vote 3"
    
    def test_minister_attendance_with_float_confidence(self):
        """Test creating minister attendance with float confidence."""
        attendance = MinisterAttendance(
            minister_id="07683",
            minute_ref="0072",
            legislature=56,
            present=False,
            confidence_score=0.85
        )
        
        assert isinstance(attendance.confidence_score, ConfidenceScore)
        assert attendance.confidence_score.value == 0.85
    
    def test_minister_attendance_without_confidence(self):
        """Test creating minister attendance without confidence score."""
        attendance = MinisterAttendance(
            minister_id="07683",
            minute_ref="0072",
            legislature=56,
            present=True
        )
        
        assert attendance.confidence_score is None
        assert not attendance.is_confident()
    
    def test_invalid_minister_id(self):
        """Test validation for empty minister ID."""
        with pytest.raises(ValueError, match="Minister ID cannot be empty"):
            MinisterAttendance(
                minister_id="",
                minute_ref="0072",
                legislature=56,
                present=True
            )
    
    def test_invalid_minute_ref(self):
        """Test validation for empty minute ref."""
        with pytest.raises(
            ValueError,
            match="Minute reference cannot be empty"
        ):
            MinisterAttendance(
                minister_id="07683",
                minute_ref="",
                legislature=56,
                present=True
            )
    
    def test_invalid_legislature(self):
        """Test validation for invalid legislature."""
        with pytest.raises(ValueError, match="Legislature must be positive"):
            MinisterAttendance(
                minister_id="07683",
                minute_ref="0072",
                legislature=0,
                present=True
            )
    
    def test_is_confident_threshold(self):
        """Test confidence threshold checking."""
        attendance = MinisterAttendance(
            minister_id="07683",
            minute_ref="0072",
            legislature=56,
            present=True,
            confidence_score=0.75
        )
        
        assert attendance.is_confident(0.7)
        assert attendance.is_confident(0.75)
        assert not attendance.is_confident(0.8)


class TestMinisterAttendanceRepository:
    """Test PostgreSQLMinisterAttendanceRepository."""
    
    # Note: These tests would require database setup
    # For now, they serve as placeholders for integration tests
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_save_minister_attendance(self):
        """Test saving a minister attendance record."""
        pass
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_find_by_minister(self):
        """Test finding attendance records for a minister."""
        pass
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_find_by_minute(self):
        """Test finding attendance records for a minute."""
        pass
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_get_attendance_summary(self):
        """Test getting attendance summary statistics."""
        pass


class TestLLMMinisterAttendanceParser:
    """Test LLMMinisterAttendanceParser."""
    
    @pytest.mark.skip(reason="Requires LLM client and database setup")
    def test_parse_minister_present(self):
        """Test parsing when minister is present."""
        pass
    
    @pytest.mark.skip(reason="Requires LLM client and database setup")
    def test_parse_minister_absent(self):
        """Test parsing when minister is absent."""
        pass
    
    @pytest.mark.skip(reason="Requires LLM client and database setup")
    def test_parse_no_vote_nominatif(self):
        """Test parsing minute without vote nominatif."""
        pass
    
    def test_has_vote_nominatif_markers(self):
        """Test detection of vote nominatif markers."""
        from infrastructure.parsers.llm_minister_attendance_parser import (
            LLMMinisterAttendanceParser
        )
        
        # Mock parser (no actual LLM client needed for this test)
        class MockLLM:
            pass
        
        class MockMatcher:
            pass
        
        parser = LLMMinisterAttendanceParser(MockLLM(), MockMatcher())
        
        # Test with vote nominatif marker
        text_with_vote = """
        Some text before
        (Stemming/vote 1)
        DETAIL VAN DE NAAMSTEMMINGEN
        Some names here
        """
        assert parser._has_vote_nominatif(text_with_vote)
        
        # Test without vote nominatif marker
        text_without_vote = """
        Some regular parliamentary text
        without any vote markers
        """
        assert not parser._has_vote_nominatif(text_without_vote)
        
        # Test case insensitivity
        text_lowercase = "this has vote nominatif somewhere"
        assert parser._has_vote_nominatif(text_lowercase)
