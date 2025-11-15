#!/usr/bin/env python3
"""
Quick integration test to verify the member prerequisite flow.
"""

import logging
from unittest.mock import Mock

from application import (
    SynchronizeMembersUseCase,
    SynchronizeMinutesUseCase
)
from infrastructure.scrapers.session_scraper import ParliamentarySessionScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def test_member_prerequisite_flow():
    """Test that member synchronization works as prerequisite."""
    logger = logging.getLogger(__name__)
    logger.info("Testing member prerequisite flow...")
    
    # Mock dependencies
    member_repo = Mock()
    member_scraper = Mock()
    
    # Simulate members already exist
    member_repo.has_members_for_legislature.return_value = True
    member_repo.count_members_for_legislature.return_value = 150
    
    # Create and execute member use case
    member_use_case = SynchronizeMembersUseCase(
        member_repo=member_repo,
        member_scraper=member_scraper
    )
    
    member_use_case.execute(legislature=56)
    
    # Verify behavior
    assert member_repo.has_members_for_legislature.called
    assert not member_scraper.scrape_members.called  # Should skip
    
    logger.info("✅ Test 1 passed: Members exist, skipped scraping")
    
    # Test 2: Members don't exist, should scrape
    member_repo.reset_mock()
    member_scraper.reset_mock()
    
    member_repo.has_members_for_legislature.return_value = False
    mock_member = Mock()
    mock_member.member_id = "123"
    mock_member.legislature = 56
    member_scraper.scrape_members.return_value = [mock_member]
    
    member_use_case.execute(legislature=56)
    
    assert member_repo.has_members_for_legislature.called
    assert member_scraper.scrape_members.called
    assert member_repo.save_members.called
    
    logger.info("✅ Test 2 passed: No members, scraped successfully")
    
    # Test 3: Verify minutes use case accepts legislature parameter
    session_repo = Mock()
    minute_repo = Mock()
    content_retriever = Mock()
    content_storage = Mock()
    
    session_repo.retrieve_all_sessions.return_value = []
    
    minute_use_case = SynchronizeMinutesUseCase(
        session_metadata_repo=session_repo,
        minute_repo=minute_repo,
        content_retriever=content_retriever,
        content_storage=content_storage
    )
    
    minute_use_case.execute(legislature=56)
    
    assert session_repo.retrieve_all_sessions.called
    
    logger.info("✅ Test 3 passed: Minutes use case accepts legislature")
    
    # Test 4: Verify session scraper uses legislature parameter
    scraper_56 = ParliamentarySessionScraper(legislature=56)
    scraper_57 = ParliamentarySessionScraper(legislature=57)
    
    assert scraper_56.legislature == 56
    assert scraper_57.legislature == 57
    assert 'legislat=56' in scraper_56.legislature_url
    assert 'legislat=57' in scraper_57.legislature_url
    
    logger.info("✅ Test 4 passed: Session scraper URLs parameterized")
    
    logger.info("🎉 All tests passed!")


if __name__ == "__main__":
    test_member_prerequisite_flow()
