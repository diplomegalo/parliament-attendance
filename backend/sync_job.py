#!/usr/bin/env python3
"""
Parliamentary Minute Synchronization - Main Entry Point.

This script sets up the dependency injection and executes the
synchronization use case following clean architecture principles.
"""

import logging
import sys
import os

from application.use_cases import (
    SynchronizeMinutesUseCase,
    SynchronizeMembersUseCase
)
from infrastructure.session_scraper import ParliamentarySessionScraper
from infrastructure.database_repository import PostgresMinuteRepository
from infrastructure.member_repository import PostgresMemberRepository
from infrastructure.member_scraper import ChamberMemberScraper
from infrastructure.local_file_storage import LocalFileSystemStorage
from infrastructure.azure_blob_storage import AzureBlobStorage

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def create_content_storage():
    """
    Create appropriate content storage based on environment.
    
    Development: Uses local filesystem storage
    Production: Uses Azure Blob Storage
    
    Returns:
        IContentStorage implementation
    """
    logger = logging.getLogger(__name__)
    storage_type = os.getenv('CONTENT_STORAGE', 'local').lower()
    
    if storage_type == 'azure':
        logger.info("Initializing Azure Blob Storage for content")
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        container_name = os.getenv('AZURE_STORAGE_CONTAINER', 'minutes')
        return AzureBlobStorage(connection_string, container_name)
    else:
        logger.info("Initializing Local File System Storage for content")
        storage_path = os.getenv('LOCAL_STORAGE_PATH', './data/minutes')
        return LocalFileSystemStorage(storage_path)


def main():
    """
    Main entry point - Dependency Injection and Use Case Execution.
    
    Sets up infrastructure adapters and executes the synchronization
    use case following clean architecture and dependency inversion.
    
    Environment Variables:
        LEGISLATURE: Legislature number to process (default: 56)
        CONTENT_STORAGE: 'local' (default) or 'azure'
        LOCAL_STORAGE_PATH: Path for local storage
                           (default: ./data/minutes)
        AZURE_STORAGE_CONNECTION_STRING: Azure connection string
                                         (required for azure)
        AZURE_STORAGE_CONTAINER: Azure container name
                                (default: minutes)
    """
    logger = logging.getLogger(__name__)
    
    # Get legislature from environment or use default
    legislature = int(os.getenv('LEGISLATURE', '56'))
    
    logger.info(
        f"🚀 Starting synchronization for legislature {legislature}"
    )
    
    try:
        # Infrastructure layer - adapters for external systems
        session_scraper = ParliamentarySessionScraper(legislature=legislature)
        database_repo = PostgresMinuteRepository()
        content_storage = create_content_storage()
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
