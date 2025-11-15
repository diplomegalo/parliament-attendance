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

from infrastructure.storage.local_content_storage import LocalContentStorage
from infrastructure.repositories.minute_repository import PostgresMinuteRepository
from infrastructure.repositories.cleaned_text_repository import PostgresCleanedTextRepository
from infrastructure.repositories.member_repository import PostgresMemberRepository
from infrastructure.repositories.attendance_repository import PostgresAttendanceRepository
from infrastructure.ai.llm_factory import LLMFactory
from infrastructure.matchers.member_name_matcher import MemberNameMatcher
from domain.repositories import (
    ILLMClient,
    LLMError,
    LLMConnectionError,
    LLMRateLimitError
)


def compute_attendance_for_minute(
    minute_ref: str,
    legislature: int,
    llm_client: ILLMClient,
    member_matcher: MemberNameMatcher,
    reprocess: bool = False
) -> bool:
    """
    Compute attendance for a single minute using LLM.
    
    Args:
        minute_ref: Minute reference (e.g., "0001")
        legislature: Legislature number
        llm_client: LLM client for text analysis
        member_matcher: Fuzzy matcher for member names
        reprocess: Whether to reprocess if already computed
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"Processing minute: {minute_ref} (Legislature {legislature})")
    print(f"{'='*80}\n")
    
    # Initialize repositories
    content_storage = LocalContentStorage()
    minute_repo = PostgresMinuteRepository()
    cleaned_text_repo = PostgresCleanedTextRepository()
    attendance_repo = PostgresAttendanceRepository()
    
    try:
        # 1. Check if already processed
        if not reprocess:
            existing_count = attendance_repo.count_by_minute(minute_ref, legislature)
            if existing_count > 0:
                print(f"⏭️  Minute {minute_ref} already has {existing_count} attendance records. Skipping.")
                print("   Use REPROCESS=true to reprocess.")
                return True
        
        # 2. Load cleaned text
        print("📖 Loading cleaned text...")
        cleaned_record = cleaned_text_repo.find_by_minute(minute_ref, legislature)
        if not cleaned_record:
            print(f"❌ No cleaned text found for minute {minute_ref}")
            return False
        
        # Load text content
        text_content = content_storage.retrieve(cleaned_record.storage_key)
        if not text_content:
            print(f"❌ Failed to load text content from {cleaned_record.storage_key}")
            return False
        
        print(f"✅ Loaded {len(text_content)} characters of cleaned text")
        
        # 3. Truncate text if too long (manage token costs)
        MAX_CHARS = 15000
        if len(text_content) > MAX_CHARS:
            print(f"⚠️  Text too long ({len(text_content)} chars), truncating to {MAX_CHARS}")
            text_content = text_content[:MAX_CHARS] + "\n\n[... text truncated for token management ...]"
        
        # 4. Prepare LLM prompt
        print("\n🤖 Preparing LLM prompt for attendance extraction...")
        prompt = f"""
You are analyzing Belgian parliamentary minutes to extract member attendance information.

Extract all parliament members mentioned in the text below. For each member, identify:
1. Their full name (as written in the text)
2. Whether they spoke during the session (true/false)
3. A confidence score (0.0-1.0) for the identification

Guidelines:
- Only include actual parliament members (MPs), not government ministers or guests
- A member is "present" if they are mentioned in any capacity during the session
- Set spoke=true only if the member actively spoke or intervened
- Be conservative with confidence scores - use 1.0 only for exact, unambiguous matches
- If you see name variations (e.g., "M. Dupont" and "Dupont"), list only once with highest confidence

Parliamentary minute text:
{text_content}

Respond with valid JSON matching this exact structure:
{{
    "members": [
        {{
            "name": "Full name as written in text",
            "spoke": true or false,
            "confidence": 0.0 to 1.0
        }}
    ]
}}
"""
        
        # 5. Extract attendance data using LLM
        print("🔍 Extracting attendance data with LLM...")
        
        schema = {
            "type": "object",
            "properties": {
                "members": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "spoke": {"type": "boolean"},
                            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                        },
                        "required": ["name", "spoke", "confidence"]
                    }
                }
            },
            "required": ["members"]
        }
        
        result = llm_client.extract_structured_data(
            prompt=prompt,
            schema=schema,
            temperature=0.0  # Deterministic for consistency
        )
        
        extracted_members = result.get("members", [])
        print(f"✅ LLM extracted {len(extracted_members)} member records")
        
        # 6. Match names to database members using fuzzy matching
        print("\n🔗 Matching names to database members...")
        matched_count = 0
        unmatched_names = []
        confidence_scores = []
        
        for member_data in extracted_members:
            name = member_data["name"]
            spoke = member_data["spoke"]
            llm_confidence = member_data["confidence"]
            
            # Try fuzzy matching
            match_result = member_matcher.find_member_by_name(name, legislature)
            
            if match_result:
                member_id, match_confidence = match_result
                
                # Combine LLM confidence with fuzzy match confidence
                # Use minimum of both as final confidence
                final_confidence = min(llm_confidence, match_confidence / 100.0)
                confidence_scores.append(final_confidence)
                
                # Store attendance record
                # TODO: Implement attendance_repo.create() method
                # attendance_repo.create(
                #     minute_ref=minute_ref,
                #     legislature=legislature,
                #     member_id=member_id,
                #     spoke=spoke,
                #     confidence=final_confidence
                # )
                
                matched_count += 1
                print(f"  ✓ Matched: {name} → Member ID {member_id} "
                      f"(LLM: {llm_confidence:.2f}, Fuzzy: {match_confidence:.0f}, Final: {final_confidence:.2f})")
            else:
                unmatched_names.append(name)
                print(f"  ✗ No match: {name} (confidence too low or not found)")
        
        # 7. Report statistics
        print(f"\n{'='*80}")
        print(f"📊 RESULTS FOR MINUTE {minute_ref}")
        print(f"{'='*80}")
        print(f"Total extracted: {len(extracted_members)}")
        print(f"Matched: {matched_count}")
        print(f"Unmatched: {len(unmatched_names)}")
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            print(f"Average confidence: {avg_confidence:.2f}")
        
        if unmatched_names:
            print(f"\nUnmatched names:")
            for name in unmatched_names[:10]:  # Show first 10
                print(f"  - {name}")
            if len(unmatched_names) > 10:
                print(f"  ... and {len(unmatched_names) - 10} more")
        
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
    
    print("🏛️  COMPUTE ATTENDANCE JOB")
    print(f"Legislature: {legislature}")
    print(f"Reprocess: {reprocess}")
    
    # Initialize LLM client
    try:
        print("\n🔧 Initializing LLM client...")
        llm_client = LLMFactory.create_client()
        print(f"✅ LLM client created successfully")
        print(f"   Available models: {', '.join(llm_client.get_available_models()[:3])}")
    except ValueError as e:
        print(f"❌ LLM Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        sys.exit(1)
    
    # Initialize member name matcher
    print("🔧 Initializing member name matcher...")
    member_repo = PostgresMemberRepository()
    member_matcher = MemberNameMatcher(member_repo, threshold=85)
    print("✅ Member matcher ready")
    
    # Process minutes
    if minute_ref:
        # Process single minute
        success = compute_attendance_for_minute(
            minute_ref=minute_ref,
            legislature=legislature,
            llm_client=llm_client,
            member_matcher=member_matcher,
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
                llm_client=llm_client,
                member_matcher=member_matcher,
                reprocess=reprocess
            )
            
            if success:
                successful += 1
            else:
                failed += 1
        
        # Final summary
        print(f"\n{'='*80}")
        print(f"🎯 FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Total minutes: {len(minutes)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"{'='*80}\n")
        
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
