"""
Extract Attendance Use Case.

Orchestrates attendance extraction from parliamentary minutes using AI.
"""

from typing import List
from domain.repositories import (
    IMinuteRepository,
    IContentStorage,
    IAttendanceRepository,
    IAttendanceParser,
    ICleanedTextRepository
)
from domain.entities import MemberPresence, CleanedMinuteText
from infrastructure.parsers import MinuteTextCleaner


class ExtractAttendanceUseCase:
    """
    Use case for extracting attendance from parliamentary minutes.
    
    Coordinates the process of:
    1. Retrieving minute content from storage
    2. Cleaning HTML to extract text
    3. Storing cleaned text in storage (orchestrated here)
    4. Storing cleaned text metadata in database
    5. Parsing attendance with AI
    6. Persisting attendance records
    """
    
    def __init__(
        self,
        minute_repository: IMinuteRepository,
        content_storage: IContentStorage,
        attendance_repository: IAttendanceRepository,
        attendance_parser: IAttendanceParser,
        cleaned_text_repository: ICleanedTextRepository
    ):
        """
        Initialize use case with dependencies.
        
        Args:
            minute_repository: Repository for minute metadata
            content_storage: Storage for HTML content
            attendance_repository: Repository for attendance records
            attendance_parser: AI parser for extracting attendance
            cleaned_text_repository: Repository for cleaned text metadata
        """
        self.minute_repository = minute_repository
        self.content_storage = content_storage
        self.attendance_repository = attendance_repository
        self.attendance_parser = attendance_parser
        self.cleaned_text_repository = cleaned_text_repository
        self.text_cleaner = MinuteTextCleaner()
    
    def execute(
        self,
        session_ref: str,
        legislature: int,
        reprocess: bool = False
    ) -> List[MemberPresence]:
        """
        Extract attendance from a parliamentary minute.
        
        Args:
            session_ref: Session reference (CRIV format)
            legislature: Legislature number
            reprocess: If True, delete existing attendance first
            
        Returns:
            List of extracted MemberPresence records
            
        Raises:
            ValueError: If minute not found or invalid
            RuntimeError: If extraction fails
        """
        # Check if minute exists
        minute = self.minute_repository.find_by_ref(session_ref)
        if not minute:
            raise ValueError(
                f"Minute not found for session {session_ref}"
            )
        
        # Delete existing attendance if reprocessing
        if reprocess:
            deleted = self.attendance_repository.delete_by_session(
                session_ref
            )
            print(
                f"Deleted {deleted} existing attendance "
                f"records for session {session_ref}"
            )
        
        # Retrieve HTML content from storage
        html_content = self.content_storage.retrieve_content(
            minute.content_storage_key
        )
        if not html_content:
            raise ValueError(
                f"Content not found for minute {session_ref}"
            )
        
        # Clean HTML to extract text (with vote filtering enabled by default)
        minute_text = self.text_cleaner.extract_text(
            html_content,
            extract_votes_only=True
        )
        
        # Skip processing if no voting sections found
        if minute_text is None:
            print(
                f"ℹ️  No voting sections found in minute {session_ref}. "
                "Skipping attendance extraction."
            )
            return []
        
        # Orchestrate storage: content in storage, metadata in DB
        # Step 1: Store cleaned text content in storage
        storage_key = self.content_storage.store_content(
            f"cleaned/{session_ref}",
            minute_text
        )
        
        # Step 2: Compute hash for traceability
        text_hash = CleanedMinuteText.compute_hash(minute_text)
        
        # Step 3: Create metadata entity
        cleaned_metadata = CleanedMinuteText.create(
            minute_ref=session_ref,
            content_storage_key=storage_key,
            text_hash=text_hash,
            cleaning_method="html_strip_voting_v1"
        )
        
        # Step 4: Save metadata to database
        self.cleaned_text_repository.save_metadata(cleaned_metadata)
        
        # Parse attendance with AI (using the cleaned text)
        presences = self.attendance_parser.parse_attendance(
            minute_text,
            session_ref,
            legislature
        )
        
        # Persist attendance records
        saved_presences = self.attendance_repository.save_batch(presences)
        
        return saved_presences
    
    def execute_batch(
        self,
        legislature: int,
        reprocess: bool = False,
        limit: int = None
    ) -> dict:
        """
        Extract attendance from multiple minutes.
        
        Processes all minutes for a legislature in batches.
        
        Args:
            legislature: Legislature number
            reprocess: If True, delete existing attendance first
            limit: Maximum number of minutes to process (for testing)
            
        Returns:
            Dictionary with processing statistics
            
        Raises:
            RuntimeError: If batch processing fails
        """
        # Get all minutes for legislature
        minutes = self.minute_repository.find_by_legislature(legislature)
        
        if limit:
            minutes = minutes[:limit]
        
        stats = {
            'total': len(minutes),
            'processed': 0,
            'failed': 0,
            'presences_extracted': 0
        }
        
        for minute in minutes:
            try:
                presences = self.execute(
                    minute.ref,
                    legislature,
                    reprocess
                )
                stats['processed'] += 1
                stats['presences_extracted'] += len(presences)
                
                print(
                    f"Processed {minute.ref}: "
                    f"{len(presences)} presences extracted"
                )
            except Exception as e:
                stats['failed'] += 1
                print(
                    f"Failed to process {minute.ref}: {str(e)}"
                )
        
        return stats
