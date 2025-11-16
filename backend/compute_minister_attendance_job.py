#!/usr/bin/env python3
"""
Compute Minister Attendance Job

Regex-based minister attendance extraction from cleaned parliamentary minutes.
Uses simple pattern matching to check if a specific minister was present
in each minute containing vote nominatif.

Usage:
    # Process single minute for a minister
    MINISTER_NAME="Alexia Bertrand" MINUTE_REF=0072 LEGISLATURE=56 \
        python compute_minister_attendance_job.py
    
    # Process all minutes for a minister
    MINISTER_NAME="Alexia Bertrand" LEGISLATURE=56 \
        python compute_minister_attendance_job.py
    
    # Reprocess already computed attendance
    MINISTER_NAME="Alexia Bertrand" LEGISLATURE=56 REPROCESS=true \
        python compute_minister_attendance_job.py
    
Environment Variables:
    MINISTER_NAME: Full name of minister (required)
    MINUTE_REF: Specific minute to process (optional)
    LEGISLATURE: Legislature number (e.g., 56)
    REPROCESS: Set to "true" to reprocess already computed attendance
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.storage.storage_factory import StorageFactory
from infrastructure.repositories.minute_repository import (
    PostgresMinuteRepository
)
from infrastructure.repositories.cleaned_text_repository import (
    PostgreSQLCleanedTextRepository
)
from infrastructure.repositories.member_repository import (
    PostgresMemberRepository
)
from infrastructure.repositories.minister_attendance_repository import (
    PostgreSQLMinisterAttendanceRepository
)
from infrastructure.matchers.member_name_matcher import MemberNameMatcher
from infrastructure.parsers.regex_minister_attendance_parser import (
    RegexMinisterAttendanceParser
)
from domain.entities.minister_attendance import MinisterAttendance


def compute_minister_attendance_for_minute(
    minute_ref: str,
    legislature: int,
    minister_name: str,
    attendance_parser: RegexMinisterAttendanceParser,
    reprocess: bool = False
) -> bool:
    """
    Compute minister attendance for a single minute using LLM.
    
    Args:
        minute_ref: Minute reference (e.g., "0001")
        legislature: Legislature number
        minister_name: Full name of minister
        attendance_parser: Parser with LLM client and member matcher
        reprocess: Whether to reprocess if already computed
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*80}")
    print(
        f"Processing minute: {minute_ref} for minister: {minister_name} "
        f"(Legislature {legislature})"
    )
    print(f"{'='*80}\n")
    
    # Initialize repositories
    content_storage = StorageFactory.create_cleaned_storage()
    cleaned_text_repo = PostgreSQLCleanedTextRepository()
    attendance_repo = PostgreSQLMinisterAttendanceRepository()
    
    try:
        # 1. Check if already processed
        if not reprocess:
            existing = attendance_repo.find_by_minute(minute_ref, legislature)
            if existing:
                print(
                    f"⏭️  Skipping {minute_ref} "
                    f"(already processed, {len(existing)} records)"
                )
                return True
        
        # 2. Load cleaned text
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
        
        # 3. Use parser to extract minister attendance
        attendance_dict = attendance_parser.parse_minister_attendance(
            minute_text=text_content,
            minute_ref=minute_ref,
            minister_name=minister_name,
            legislature=legislature
        )
        
        # 4. Check if minute has vote nominatif
        if attendance_dict is None:
            print(f"⏭️  Minute {minute_ref} has no vote nominatif, skipping")
            return True
        
        # 5. Save to database
        attendance = MinisterAttendance(**attendance_dict)
        saved_attendance = attendance_repo.save(attendance)
        
        print(
            f"💾 Saved minister attendance: "
            f"present={saved_attendance.present}, "
            f"confidence={saved_attendance.confidence_score}"
        )
        
        # 6. Report result
        print(f"\n{'='*80}")
        print(f"📊 RESULT FOR MINUTE {minute_ref}")
        print(f"{'='*80}")
        print(f"Minister: {minister_name}")
        print(f"Present: {saved_attendance.present}")
        print(
            f"Confidence: "
            f"{saved_attendance.confidence_score.value:.2f}"
            if saved_attendance.confidence_score else "N/A"
        )
        if saved_attendance.context:
            print(f"Context: {saved_attendance.context}")
        print(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for compute minister attendance job."""
    
    # Parse environment variables
    minister_name = os.getenv("MINISTER_NAME")
    if not minister_name:
        print("❌ MINISTER_NAME environment variable is required")
        sys.exit(1)
    
    minute_ref = os.getenv("MINUTE_REF")
    legislature = int(os.getenv("LEGISLATURE", "56"))
    reprocess = os.getenv("REPROCESS", "").lower() == "true"
    
    print("🏛️  COMPUTE MINISTER ATTENDANCE JOB")
    print(f"Minister: {minister_name}")
    print(f"Legislature: {legislature}")
    print(f"Reprocess: {reprocess}")
    
    # Initialize member name matcher and parser (no LLM needed)
    print("\n🔧 Initializing member name matcher...")
    member_repo = PostgresMemberRepository()
    member_matcher = MemberNameMatcher(member_repo, threshold=85)
    print("✅ Member matcher ready")
    
    print("🔧 Initializing regex minister attendance parser...")
    attendance_parser = RegexMinisterAttendanceParser(member_matcher)
    print("✅ Minister attendance parser ready")
    
    # Process minutes
    if minute_ref:
        # Process single minute
        success = compute_minister_attendance_for_minute(
            minute_ref=minute_ref,
            legislature=legislature,
            minister_name=minister_name,
            attendance_parser=attendance_parser,
            reprocess=reprocess
        )
        sys.exit(0 if success else 1)
    else:
        # Process all minutes for legislature
        print(
            f"\n📋 Processing all minutes for legislature {legislature}..."
        )
        minute_repo = PostgresMinuteRepository()
        minutes = minute_repo.find_by_legislature(legislature)
        
        print(f"Found {len(minutes)} minutes to process\n")
        
        successful = 0
        failed = 0
        skipped = 0
        
        for minute in minutes:
            success = compute_minister_attendance_for_minute(
                minute_ref=minute.get_reference(),
                legislature=legislature,
                minister_name=minister_name,
                attendance_parser=attendance_parser,
                reprocess=reprocess
            )
            
            if success:
                # Check if actually processed or skipped
                cleaned_text_repo = PostgreSQLCleanedTextRepository()
                cleaned_record = cleaned_text_repo.find_by_minute_ref(
                    minute.get_reference()
                )
                if cleaned_record:
                    successful += 1
                else:
                    skipped += 1
            else:
                failed += 1
        
        # Final summary
        print(f"\n{'='*80}")
        print("🎯 FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Minister: {minister_name}")
        print(f"Total minutes: {len(minutes)}")
        print(f"Successful: {successful}")
        print(f"Skipped (no vote nominatif): {skipped}")
        print(f"Failed: {failed}")
        print(f"{'='*80}\n")
        
        # Get attendance summary
        attendance_repo = PostgreSQLMinisterAttendanceRepository()
        member_repo = PostgresMemberRepository()
        
        # Match minister name to get ID
        member_matcher = MemberNameMatcher(member_repo, threshold=85)
        match = member_matcher.find_member_by_name(minister_name, legislature)
        
        if match:
            minister_id, _ = match
            summary = attendance_repo.get_attendance_summary(
                minister_id,
                legislature
            )
            
            print(f"📊 ATTENDANCE SUMMARY FOR {minister_name}")
            print(f"{'='*80}")
            print(f"Total minutes with votes: {summary['total_minutes']}")
            print(f"Present: {summary['present_count']}")
            print(f"Absent: {summary['absent_count']}")
            print(
                f"Attendance rate: {summary['attendance_rate']:.2f}%"
            )
            print(f"{'='*80}\n")
        
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
