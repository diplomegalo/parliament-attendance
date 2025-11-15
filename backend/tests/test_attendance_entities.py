"""
Tests for attendance domain entities.

Tests MemberPresence and Vote entities with validation.
"""

import unittest
from datetime import date
from domain.entities import (
    MemberPresence,
    Vote,
    MemberVote,
)
from domain.value_objects import VotePosition, ConfidenceScore


class TestMemberPresence(unittest.TestCase):
    """Test MemberPresence entity."""
    
    def test_create_valid_presence(self):
        """Test creating a valid presence record."""
        presence = MemberPresence(
            member_id="05001001",
            session_ref="0001",
            spoke=True,
            interventions_count=3,
            confidence_score=ConfidenceScore(0.95)
        )
        
        self.assertEqual(presence.member_id, "05001001")
        self.assertEqual(presence.session_ref, "0001")
        self.assertTrue(presence.spoke)
        self.assertEqual(presence.interventions_count, 3)
        self.assertEqual(float(presence.confidence_score), 0.95)
        self.assertIsNone(presence.id)
    
    def test_create_with_float_confidence(self):
        """Test creating presence with float converts to ConfidenceScore."""
        presence = MemberPresence(
            member_id="05001001",
            session_ref="0001",
            confidence_score=0.85
        )
        
        self.assertIsInstance(presence.confidence_score, ConfidenceScore)
        self.assertEqual(float(presence.confidence_score), 0.85)
    
    def test_empty_member_id_raises_error(self):
        """Test that empty member_id raises ValueError."""
        with self.assertRaises(ValueError):
            MemberPresence(
                member_id="",
                session_ref="0001"
            )
    
    def test_empty_session_ref_raises_error(self):
        """Test that empty session_ref raises ValueError."""
        with self.assertRaises(ValueError):
            MemberPresence(
                member_id="05001001",
                session_ref=""
            )
    
    def test_negative_interventions_raises_error(self):
        """Test that negative interventions_count raises ValueError."""
        with self.assertRaises(ValueError):
            MemberPresence(
                member_id="05001001",
                session_ref="0001",
                interventions_count=-1
            )
    
    def test_is_confident(self):
        """Test confidence checking."""
        high_confidence = MemberPresence(
            member_id="05001001",
            session_ref="0001",
            confidence_score=ConfidenceScore(0.9)
        )
        self.assertTrue(high_confidence.is_confident())
        
        low_confidence = MemberPresence(
            member_id="05001001",
            session_ref="0001",
            confidence_score=ConfidenceScore(0.5)
        )
        self.assertFalse(low_confidence.is_confident())
        
        no_confidence = MemberPresence(
            member_id="05001001",
            session_ref="0001"
        )
        self.assertFalse(no_confidence.is_confident())


class TestVote(unittest.TestCase):
    """Test Vote entity."""
    
    def test_create_valid_vote(self):
        """Test creating a valid vote record."""
        vote = Vote(
            session_ref="0001",
            vote_topic="Budget 2024",
            vote_date=date(2024, 1, 15)
        )
        
        self.assertEqual(vote.session_ref, "0001")
        self.assertEqual(vote.vote_topic, "Budget 2024")
        self.assertEqual(vote.vote_date, date(2024, 1, 15))
        self.assertIsNone(vote.id)
    
    def test_empty_session_ref_raises_error(self):
        """Test that empty session_ref raises ValueError."""
        with self.assertRaises(ValueError):
            Vote(
                session_ref="",
                vote_topic="Budget 2024",
                vote_date=date(2024, 1, 15)
            )
    
    def test_empty_vote_topic_raises_error(self):
        """Test that empty vote_topic raises ValueError."""
        with self.assertRaises(ValueError):
            Vote(
                session_ref="0001",
                vote_topic="",
                vote_date=date(2024, 1, 15)
            )


class TestMemberVote(unittest.TestCase):
    """Test MemberVote entity."""
    
    def test_create_valid_member_vote(self):
        """Test creating a valid member vote record."""
        member_vote = MemberVote(
            vote_id=1,
            member_id="05001001",
            position=VotePosition.YES,
            confidence_score=ConfidenceScore(0.95)
        )
        
        self.assertEqual(member_vote.vote_id, 1)
        self.assertEqual(member_vote.member_id, "05001001")
        self.assertEqual(member_vote.position, VotePosition.YES)
        self.assertEqual(float(member_vote.confidence_score), 0.95)
        self.assertIsNone(member_vote.id)
    
    def test_create_with_float_confidence(self):
        """Test creating member vote with float converts to ConfidenceScore."""
        member_vote = MemberVote(
            vote_id=1,
            member_id="05001001",
            position=VotePosition.NO,
            confidence_score=0.75
        )
        
        self.assertIsInstance(member_vote.confidence_score, ConfidenceScore)
        self.assertEqual(float(member_vote.confidence_score), 0.75)
    
    def test_vote_position_enum(self):
        """Test VotePosition enum values."""
        self.assertEqual(VotePosition.YES.value, "yes")
        self.assertEqual(VotePosition.NO.value, "no")
        self.assertEqual(VotePosition.ABSTAIN.value, "abstain")
    
    def test_empty_member_id_raises_error(self):
        """Test that empty member_id raises ValueError."""
        with self.assertRaises(ValueError):
            MemberVote(
                vote_id=1,
                member_id="",
                position=VotePosition.YES
            )
    
    def test_invalid_vote_id_raises_error(self):
        """Test that invalid vote_id raises ValueError."""
        with self.assertRaises(ValueError):
            MemberVote(
                vote_id=0,
                member_id="05001001",
                position=VotePosition.YES
            )
    
    def test_is_confident(self):
        """Test confidence checking."""
        high_confidence = MemberVote(
            vote_id=1,
            member_id="05001001",
            position=VotePosition.YES,
            confidence_score=ConfidenceScore(0.85)
        )
        self.assertTrue(high_confidence.is_confident())
        
        low_confidence = MemberVote(
            vote_id=1,
            member_id="05001001",
            position=VotePosition.NO,
            confidence_score=ConfidenceScore(0.6)
        )
        self.assertFalse(low_confidence.is_confident())


if __name__ == '__main__':
    unittest.main()
