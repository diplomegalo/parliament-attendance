"""
Tests for value objects.

Tests immutable value objects with validation.
"""

import unittest
from domain.value_objects import (
    SessionReference,
    VotePosition,
    Legislature,
    ConfidenceScore
)


class TestSessionReference(unittest.TestCase):
    """Test SessionReference value object."""
    
    def test_create_valid_reference(self):
        """Test creating a valid session reference."""
        ref = SessionReference("0001")
        self.assertEqual(ref.value, "0001")
        self.assertEqual(str(ref), "0001")
    
    def test_immutable(self):
        """Test that SessionReference is immutable."""
        ref = SessionReference("0001")
        with self.assertRaises(AttributeError):
            ref.value = "0002"
    
    def test_empty_value_raises_error(self):
        """Test that empty value raises ValueError."""
        with self.assertRaises(ValueError):
            SessionReference("")
        
        with self.assertRaises(ValueError):
            SessionReference("   ")


class TestVotePosition(unittest.TestCase):
    """Test VotePosition enum."""
    
    def test_enum_values(self):
        """Test enum values."""
        self.assertEqual(VotePosition.YES.value, "yes")
        self.assertEqual(VotePosition.NO.value, "no")
        self.assertEqual(VotePosition.ABSTAIN.value, "abstain")
    
    def test_string_representation(self):
        """Test string representation."""
        self.assertEqual(str(VotePosition.YES), "yes")
        self.assertEqual(str(VotePosition.NO), "no")
        self.assertEqual(str(VotePosition.ABSTAIN), "abstain")


class TestLegislature(unittest.TestCase):
    """Test Legislature value object."""
    
    def test_create_valid_legislature(self):
        """Test creating a valid legislature."""
        leg = Legislature(56)
        self.assertEqual(leg.number, 56)
        self.assertEqual(str(leg), "56")
        self.assertEqual(int(leg), 56)
    
    def test_immutable(self):
        """Test that Legislature is immutable."""
        leg = Legislature(56)
        with self.assertRaises(AttributeError):
            leg.number = 57
    
    def test_negative_number_raises_error(self):
        """Test that negative number raises ValueError."""
        with self.assertRaises(ValueError):
            Legislature(-1)
    
    def test_zero_raises_error(self):
        """Test that zero raises ValueError."""
        with self.assertRaises(ValueError):
            Legislature(0)


class TestConfidenceScore(unittest.TestCase):
    """Test ConfidenceScore value object."""
    
    def test_create_valid_score(self):
        """Test creating a valid confidence score."""
        score = ConfidenceScore(0.85)
        self.assertEqual(score.value, 0.85)
        self.assertEqual(float(score), 0.85)
    
    def test_immutable(self):
        """Test that ConfidenceScore is immutable."""
        score = ConfidenceScore(0.75)
        with self.assertRaises(AttributeError):
            score.value = 0.90
    
    def test_min_max_values(self):
        """Test boundary values."""
        min_score = ConfidenceScore(0.0)
        self.assertEqual(min_score.value, 0.0)
        
        max_score = ConfidenceScore(1.0)
        self.assertEqual(max_score.value, 1.0)
    
    def test_out_of_range_raises_error(self):
        """Test that out of range values raise ValueError."""
        with self.assertRaises(ValueError):
            ConfidenceScore(-0.1)
        
        with self.assertRaises(ValueError):
            ConfidenceScore(1.5)
    
    def test_is_confident(self):
        """Test confidence threshold checking."""
        high = ConfidenceScore(0.85)
        self.assertTrue(high.is_confident())
        self.assertTrue(high.is_confident(0.7))
        self.assertTrue(high.is_confident(0.8))
        
        low = ConfidenceScore(0.6)
        self.assertFalse(low.is_confident())
        self.assertFalse(low.is_confident(0.7))
        self.assertTrue(low.is_confident(0.5))
    
    def test_string_representation(self):
        """Test string formatting as percentage."""
        score = ConfidenceScore(0.853)
        # Should format as percentage
        self.assertIn("85", str(score))


if __name__ == '__main__':
    unittest.main()
