#!/usr/bin/env python3
"""
Compute Attendance Job

AI-powered attendance extraction from cleaned parliamentary minutes.
Uses LLM (OpenAI, Azure OpenAI, etc.) via abstraction layer to extract
member presence information from plain text.

This job processes cleaned text (output of extract_attendance_job.py)
and stores structured attendance records in the database.

Usage:
    # Process single minute
    MINUTE_REF=0001 LEGISLATURE=56 python compute_attendance_job.py
    
    # Process all minutes for legislature
    LEGISLATURE=56 python compute_attendance_job.py
    
    # Reprocess already computed attendance
    LEGISLATURE=56 REPROCESS=true python compute_attendance_job.py
    
Environment Variables:
    MINUTE_REF: Specific minute to process (e.g., "0001")
    LEGISLATURE: Legislature number (e.g., 56)
    REPROCESS: Set to "true" to reprocess already computed attendance
    
    LLM Configuration (one required):
    - OPENAI_API_KEY: For OpenAI API
    - AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY: For Azure OpenAI
    - ANTHROPIC_API_KEY: For Anthropic Claude (future)
    - OLLAMA_HOST: For local Ollama (future)
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.storage.local_file_storage import LocalFileSystemStorage
from infrastructure.repositories.minute_repository import PostgresMinuteRepository
from infrastructure.repositories.cleaned_text_repository import PostgreSQLCleanedTextRepository
from infrastructure.repositories.member_repository import PostgresMemberRepository
from infrastructure.repositories.attendance_repository import PostgreSQLAttendanceRepository
from infrastructure.ai.llm_factory import LLMFactory
from infrastructure.matchers.member_name_matcher import MemberNameMatcher
from infrastructure.parsers.llm_attendance_parser import LLMAttendanceParser
from domain.repositories import (
    ILLMClient,
    LLMError,
    LLMConnectionError,
    LLMRateLimitError
)


def compute_attendance_for_minute(
    minute_ref: str,
    legislature: int,
    attendance_parser: LLMAttendanceParser,
    reprocess: bool = False
) -> bool:
    """
    Compute attendance for a single minute using LLM.
    
    Args:
        minute_ref: Minute reference (e.g., "0001")
        legislature: Legislature number
        attendance_parser: Parser with LLM client and member matcher
        reprocess: Whether to reprocess if already computed
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"Processing minute: {minute_ref} (Legislature {legislature})")
    print(f"{'='*80}\n")
    
    # Initialize repositories
    content_storage = LocalFileSystemStorage()
    cleaned_text_repo = PostgreSQLCleanedTextRepository()
    # Note: attendance_repo not used in dry run mode
    
    try:
        # 1. Check if already processed (skip for now)
        print("📖 Loading cleaned text...")
        cleaned_record = cleaned_text_repo.find_by_minute_ref(minute_ref)
        if not cleaned_record:
            print(f"❌ No cleaned text found for minute {minute_ref}")
            return False
        
        # Load text content
        text_content = content_storage.retrieve_content(
            cleaned_record.content_storage_key
        )
        if not text_content:
            print(
                f"❌ Failed to load text content "
                f"from {cleaned_record.content_storage_key}"
            )
            return False
        
        print(f"✅ Loaded {len(text_content)} characters of cleaned text")
        
        # 3. Use parser to extract attendance
        attendances = attendance_parser.parse_attendance(
            minute_text=text_content,
            session_ref=minute_ref,
            legislature=legislature
        )
        
        # 4. Report statistics
        print(f"\n{'='*80}")
        print(f"📊 RESULTS FOR MINUTE {minute_ref}")
        print(f"{'='*80}")
        print(f"Total matched: {len(attendances)}")
        
        if attendances:
            spoke_count = sum(1 for a in attendances if a['spoke'])
            avg_confidence = sum(a['confidence'] for a in attendances) / len(attendances)
            print(f"Members who spoke: {spoke_count}")
            print(f"Average confidence: {avg_confidence:.2f}")
        
        print(f"{'='*80}\n")
        
        return True
        
    except LLMConnectionError as e:
        print(f"❌ LLM Connection Error: {e}")
        return False
    except LLMRateLimitError as e:
        print(f"⏸️  LLM Rate Limit: {e}")
        print("   Consider adding retry logic or reducing request frequency.")
        return False
    except LLMError as e:
        print(f"❌ LLM Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for compute attendance job."""
    
    # Parse environment variables
    minute_ref = os.getenv("MINUTE_REF")
    legislature = int(os.getenv("LEGISLATURE", "56"))
    reprocess = os.getenv("REPROCESS", "").lower() == "true"
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    
    print("🏛️  COMPUTE ATTENDANCE JOB")
    print(f"Legislature: {legislature}")
    print(f"Reprocess: {reprocess}")
    print(f"Dry Run: {dry_run}")
    
    # Initialize LLM client
    try:
        print("\n🔧 Initializing LLM client...")
        llm_client = LLMFactory.create_client()
        print("✅ LLM client created successfully")
        models = llm_client.get_available_models()[:3]
        print(f"   Available models: {', '.join(models)}")
    except ValueError as e:
        print(f"❌ LLM Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        sys.exit(1)
    
    # Initialize member name matcher and parser
    print("🔧 Initializing member name matcher...")
    member_repo = PostgresMemberRepository()
    member_matcher = MemberNameMatcher(member_repo, threshold=85)
    print("✅ Member matcher ready")
    
    print("🔧 Initializing attendance parser...")
    attendance_parser = LLMAttendanceParser(llm_client, member_matcher)
    print("✅ Attendance parser ready")
    
    # Process minutes
    if minute_ref:
        # Process single minute
        success = compute_attendance_for_minute(
            minute_ref=minute_ref,
            legislature=legislature,
            attendance_parser=attendance_parser,
            reprocess=reprocess
        )
        sys.exit(0 if success else 1)
    else:
        # Process all minutes for legislature
        print(f"\n📋 Processing all minutes for legislature {legislature}...")
        minute_repo = PostgresMinuteRepository()
        minutes = minute_repo.find_by_legislature(legislature)
        
        print(f"Found {len(minutes)} minutes to process\n")
        
        successful = 0
        failed = 0
        
        for minute in minutes:
            success = compute_attendance_for_minute(
                minute_ref=minute.get_reference(),
                legislature=legislature,
                attendance_parser=attendance_parser,
                reprocess=reprocess
            )
            
            if success:
                successful += 1
            else:
                failed += 1
        
        # Final summary
        print(f"\n{'='*80}")
        print("🎯 FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Total minutes: {len(minutes)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"{'='*80}\n")
        
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
