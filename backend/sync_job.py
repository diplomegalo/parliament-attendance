#!/usr/bin/env python3
"""
Parliamentary Minute Synchronization - Main Entry Point.

This script sets up the dependency injection and executes the
synchronization use case following clean architecture principles.
"""

import logging
import sys
import os

from application import (
    SynchronizeMinutesUseCase,
    SynchronizeMembersUseCase
)
from infrastructure.scrapers.session_scraper import ParliamentarySessionScraper
from infrastructure.repositories.minute_repository import PostgresMinuteRepository
from infrastructure.repositories.member_repository import PostgresMemberRepository
from infrastructure.scrapers.member_scraper import ChamberMemberScraper
from infrastructure.storage.storage_factory import StorageFactory

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    """
    Main entry point - Dependency Injection and Use Case Execution.
    
    Sets up infrastructure adapters and executes the synchronization
    use case following clean architecture and dependency inversion.
    
    Environment Variables:
        LEGISLATURE: Legislature number to process (default: 56)
        CONTENT_STORAGE: 'local' (default) or 'azure'
        LOCAL_STORAGE_PATH: Base path for local storage
        AZURE_STORAGE_CONNECTION_STRING: Azure connection string
        AZURE_STORAGE_CONTAINER: Azure container name (default: parliament)
        MINUTES_STORAGE_NAME: Storage name for minutes (default: minutes)
    """
    logger = logging.getLogger(__name__)
    
    # Get legislature from environment or use default
    legislature = int(os.getenv('LEGISLATURE', '56'))
    
    logger.info(
        f"🚀 Starting synchronization for legislature {legislature}"
    )
    
    try:
        # Infrastructure layer - adapters for external systems
        session_scraper = ParliamentarySessionScraper(
            legislature=legislature
        )
        database_repo = PostgresMinuteRepository()
        content_storage = StorageFactory.create_minutes_storage()
        member_repo = PostgresMemberRepository()
        member_scraper = ChamberMemberScraper()
        
        # Step 1: Synchronize members (prerequisite check)
        logger.info("Step 1: Synchronizing members")
        member_use_case = SynchronizeMembersUseCase(
            member_repo=member_repo,
            member_scraper=member_scraper
        )
        member_use_case.execute(legislature)
        
        # Step 2: Synchronize minutes
        logger.info("Step 2: Synchronizing minutes")
        minute_use_case = SynchronizeMinutesUseCase(
            session_metadata_repo=session_scraper,
            minute_repo=database_repo,
            content_retriever=session_scraper,
            content_storage=content_storage
        )
        minute_use_case.execute(legislature)
        
        logger.info("✅ Synchronization completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Synchronization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
