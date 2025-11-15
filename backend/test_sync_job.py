#!/usr/bin/env python3
"""
Test script for sync job - runs a dry-run simulation.

This script simulates the sync job execution without actually
saving data to verify the scraping and business logic work correctly.
"""

import logging
from application.use_cases import SynchronizeMinutesUseCase
from infrastructure.session_scraper import ParliamentarySessionScraper
from infrastructure.local_file_storage import LocalFileSystemStorage

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MockMinuteRepository:
    """Mock repository that doesn't require database."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.saved_minutes = []
    
    def save_minutes(self, minutes):
        """Store minutes in memory instead of database."""
        self.saved_minutes.extend(minutes)
        self.logger.info(f"✅ Would save {len(minutes)} minutes to database")
        for minute in minutes:
            self.logger.info(
                f"   - {minute.get_reference()}: {minute.metadata.description} "
                f"({'provisional' if minute.is_provisional() else 'definitive'})"
            )
    
    def find_existing_references(self, references):
        """Return empty set - assume nothing exists yet."""
        self.logger.info(f"Checking {len(references)} references (mock: returning none exist)")
        return set()


def main():
    """Test the sync job without database."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("🧪 TESTING PARLIAMENTARY MINUTE SYNCHRONIZATION (DRY RUN)")
    logger.info("=" * 80)
    
    try:
        # Infrastructure layer
        logger.info("\n📡 Initializing session scraper...")
        session_scraper = ParliamentarySessionScraper()
        
        logger.info("💾 Initializing local storage...")
        content_storage = LocalFileSystemStorage('./data/test_minutes')
        
        logger.info("🗄️  Using mock database repository (no actual DB writes)")
        mock_repo = MockMinuteRepository()
        
        # Application layer
        logger.info("\n⚙️  Setting up use case with dependencies...")
        use_case = SynchronizeMinutesUseCase(
            session_metadata_repo=session_scraper,
            minute_repo=mock_repo,
            content_retriever=session_scraper,
            content_storage=content_storage
        )
        
        # Execute
        logger.info("\n🚀 Executing synchronization use case...")
        logger.info("-" * 80)
        use_case.execute()
        logger.info("-" * 80)
        
        # Summary
        logger.info("\n📊 SUMMARY:")
        logger.info(f"   Total minutes processed: {len(mock_repo.saved_minutes)}")
        logger.info(f"   Provisional: {sum(1 for m in mock_repo.saved_minutes if m.is_provisional())}")
        logger.info(f"   Definitive: {sum(1 for m in mock_repo.saved_minutes if m.is_definitive())}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error(f"❌ TEST FAILED: {e}")
        logger.error("=" * 80, exc_info=True)
        raise


if __name__ == "__main__":
    main()
