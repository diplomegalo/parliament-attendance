#!/usr/bin/env python3
"""
Parliamentary Attendance Extraction - Job Entry Point.

This script extracts attendance data from parliamentary minutes
using AI-powered text analysis. It processes cleaned text and
stores attendance records in the database.
"""

import logging
import os

from infrastructure.repositories.minute_repository import (
    PostgresMinuteRepository
)
from infrastructure.repositories.cleaned_text_repository import (
    PostgreSQLCleanedTextRepository
)
from infrastructure.storage.storage_factory import StorageFactory
from domain.entities import CleanedMinuteText

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



def main():
    """
    Main entry point - Extract attendance from parliamentary minutes.
    
    Currently only processes and stores cleaned text.
    TODO: Add AI-powered attendance extraction.
    
    Environment Variables:
        LEGISLATURE: Legislature number to process (default: 56)
        MINUTE_REF: Specific minute to process
                    (optional, processes all if not set)
        EXTRACT_VOTES_ONLY: 'true' (default) or 'false'
                           Extract only voting sections to reduce tokens
        CONTENT_STORAGE: 'local' (default) or 'azure'
        LOCAL_STORAGE_PATH: Path for local storage
                           (default: ./data/minutes)
        AZURE_STORAGE_CONNECTION_STRING: Azure connection string
        AZURE_STORAGE_CONTAINER: Azure container name (default: minutes)
    """
    logger = logging.getLogger(__name__)
    
    # Get parameters from environment
    legislature = int(os.getenv('LEGISLATURE', '56'))
    minute_ref = os.getenv('MINUTE_REF')
    extract_votes_only = os.getenv('EXTRACT_VOTES_ONLY', 'true').lower() == 'true'
    
    if minute_ref:
        logger.info(
            f"🚀 Starting text cleaning for minute {minute_ref} "
            f"(legislature {legislature})"
        )
    else:
        logger.info(
            f"🚀 Starting text cleaning for all minutes "
            f"(legislature {legislature})"
        )
    
    if extract_votes_only:
        logger.info("📊 Vote extraction mode: Only voting sections will be extracted")
    else:
        logger.info("📄 Full text mode: Complete minutes will be extracted")
    
    try:
        # Infrastructure layer - adapters for external systems
        minute_repo = PostgresMinuteRepository()
        content_storage = StorageFactory.create_cleaned_storage()
        cleaned_text_repo = PostgreSQLCleanedTextRepository()
        
        # Import here to avoid unused import errors
        from infrastructure.parsers.minute_text_cleaner import (
            MinuteTextCleaner
        )
        text_cleaner = MinuteTextCleaner()
        
        if minute_ref:
            # Process single minute
            logger.info(f"Processing minute {minute_ref}")
            
            # 1. Retrieve minute metadata to get storage key
            minutes = minute_repo.find_by_legislature(legislature)
            minute = next(
                (m for m in minutes if m.get_reference() == minute_ref),
                None
            )
            
            if not minute:
                logger.error(f"Minute {minute_ref} not found")
                import sys
                sys.exit(1)
            
            # 2. Retrieve HTML content
            html_content = content_storage.retrieve_content(
                minute.content_storage_key
            )
            logger.info(
                f"Retrieved HTML content: {len(html_content)} characters"
            )
            
            # 2. Clean HTML to text
            cleaned_text = text_cleaner.extract_text(
                html_content,
                extract_votes_only=extract_votes_only
            )
            
            if cleaned_text is None:
                logger.warning(
                    f"⚠️  No voting sections found in minute {minute_ref}. Skipping."
                )
                return
            
            logger.info(
                f"Cleaned text: {len(cleaned_text)} characters"
            )
            
            # 3. Store cleaned text in storage
            storage_key = content_storage.store_content(
                f"cleaned/{minute_ref}.txt",
                cleaned_text
            )
            logger.info(f"Stored cleaned text: {storage_key}")
            
            # 4. Compute hash
            text_hash = CleanedMinuteText.compute_hash(cleaned_text)
            logger.info(f"Computed hash: {text_hash[:16]}...")
            
            # 5. Create metadata entity
            cleaning_method = "html_strip_voting_v1" if extract_votes_only else "html_strip_v1"
            metadata = CleanedMinuteText.create(
                minute_ref=minute_ref,
                content_storage_key=storage_key,
                text_hash=text_hash,
                cleaning_method=cleaning_method
            )
            
            # 6. Save metadata to database
            result = cleaned_text_repo.save_metadata(metadata)
            logger.info(
                f"✅ Successfully processed minute {minute_ref}: "
                f"Cleaned text stored with hash {result.text_hash[:8]}..."
            )
        else:
            # Process all minutes for legislature
            logger.info(f"Fetching all minutes for legislature {legislature}")
            minutes = minute_repo.find_by_legislature(legislature)
            
            if not minutes:
                logger.warning(
                    f"No minutes found for legislature {legislature}"
                )
                return
            
            logger.info(f"Found {len(minutes)} minutes to process")
            
            processed = 0
            failed = 0
            skipped = 0
            
            for minute in minutes:
                try:
                    # Check if already processed
                    if cleaned_text_repo.exists(minute.get_reference()):
                        logger.info(
                            f"⏭️  Skipping {minute.get_reference()} "
                            "(already processed)"
                        )
                        skipped += 1
                        continue
                    
                    logger.info(f"Processing minute {minute.get_reference()}")
                    
                    # 1. Retrieve HTML
                    html_content = content_storage.retrieve_content(
                        minute.content_storage_key
                    )
                    
                    # 2. Clean HTML
                    cleaned_text = text_cleaner.extract_text(
                        html_content,
                        extract_votes_only=extract_votes_only
                    )
                    
                    # Skip if no voting sections found
                    if cleaned_text is None:
                        logger.warning(
                            f"⚠️  No voting sections found in minute "
                            f"{minute.get_reference()}. Skipping."
                        )
                        skipped += 1
                        continue
                    
                    # 3. Store cleaned text
                    storage_key = content_storage.store_content(
                        f"cleaned/{minute.get_reference()}.txt",
                        cleaned_text
                    )
                    
                    # 4. Compute hash
                    text_hash = CleanedMinuteText.compute_hash(cleaned_text)
                    
                    # 5. Create metadata
                    cleaning_method = "html_strip_voting_v1" if extract_votes_only else "html_strip_v1"
                    metadata = CleanedMinuteText.create(
                        minute_ref=minute.get_reference(),
                        content_storage_key=storage_key,
                        text_hash=text_hash,
                        cleaning_method=cleaning_method
                    )
                    
                    # 6. Save metadata
                    result = cleaned_text_repo.save_metadata(metadata)
                    logger.info(
                        f"✅ Processed {minute.get_reference()}: "
                        f"hash {result.text_hash[:8]}..."
                    )
                    processed += 1
                    
                except Exception as e:
                    logger.error(
                        f"❌ Failed to process minute "
                        f"{minute.get_reference()}: {e}"
                    )
                    failed += 1
            
            logger.info(
                f"✅ Batch processing completed: "
                f"{processed} processed, {skipped} skipped, {failed} failed"
            )
        
    except Exception as e:
        logger.error(f"❌ Text cleaning failed: {e}", exc_info=True)
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
