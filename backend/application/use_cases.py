"""
Use case: Synchronize Parliamentary Minutes.

This use case orchestrates the business logic for retrieving and storing
parliamentary session minutes. It follows the single responsibility principle
and depends only on domain abstractions (repository interfaces).
"""

import logging
from typing import List
from domain.entities import ParliamentaryMinute, SessionMetadata
from domain.repositories import (
    ISessionMetadataRepository,
    IMinuteRepository,
    IMinuteContentRetriever,
    IContentStorage,
    IMemberRepository,
    IMemberScraper
)


class SynchronizeMembersUseCase:
    """
    Use case for synchronizing parliament members.
    
    Ensures member data exists for a specific legislature
    before processing minutes.
    """
    
    def __init__(
        self,
        member_repo: IMemberRepository,
        member_scraper: IMemberScraper
    ):
        """
        Initialize with member dependencies.
        
        Args:
            member_repo: Repository for member database operations
            member_scraper: Service for scraping member data
        """
        self.member_repo = member_repo
        self.member_scraper = member_scraper
        self.logger = logging.getLogger(__name__)
    
    def execute(self, legislature: int) -> None:
        """
        Execute member synchronization for a legislature.
        
        Args:
            legislature: Legislature number to synchronize
        """
        self.logger.info(
            f"Checking members for legislature {legislature}"
        )
        
        if self.member_repo.has_members_for_legislature(legislature):
            count = self.member_repo.count_members_for_legislature(
                legislature
            )
            self.logger.info(
                f"✅ Members already exist for legislature "
                f"{legislature} ({count} members)"
            )
            return
        
        self.logger.warning(
            f"⚠️  No members found for legislature {legislature}. "
            f"Scraping member list..."
        )
        
        try:
            members = self.member_scraper.scrape_members(legislature)
            
            if not members:
                raise ValueError(
                    f"No members scraped for legislature {legislature}"
                )
            
            self.member_repo.save_members(members)
            
            self.logger.info(
                f"✅ Successfully scraped and saved {len(members)} "
                f"members for legislature {legislature}"
            )
            
        except Exception as e:
            self.logger.error(
                f"❌ Failed to scrape members for "
                f"legislature {legislature}: {e}"
            )
            raise RuntimeError(
                f"Cannot proceed without member data "
                f"for legislature {legislature}"
            ) from e


class SynchronizeMinutesUseCase:
    """
    Use case for synchronizing parliamentary minutes.
    
    Business rules:
    - Always process provisional sessions (they can be updated)
    - Only process definitive sessions that don't exist yet
    - Retrieve full content for each session
    - Store content in separate storage (filesystem or blob)
    - Store metadata in database
    """
    
    def __init__(
        self,
        session_metadata_repo: ISessionMetadataRepository,
        minute_repo: IMinuteRepository,
        content_retriever: IMinuteContentRetriever,
        content_storage: IContentStorage
    ):
        """
        Initialize use case with required dependencies.
        
        Args:
            session_metadata_repo: Repository for session metadata
            minute_repo: Repository for storing/retrieving minutes
            content_retriever: Service for retrieving minute content
            content_storage: Service for storing large content files
        """
        self.session_metadata_repo = session_metadata_repo
        self.minute_repo = minute_repo
        self.content_retriever = content_retriever
        self.content_storage = content_storage
        self.logger = logging.getLogger(__name__)
    
    def execute(self, legislature: int) -> None:
        """
        Execute the synchronization use case.
        
        Args:
            legislature: Legislature number to process
        
        Steps:
        1. Retrieve all session metadata
        2. Filter sessions based on business rules
        3. Retrieve full content for each session
        4. Save all minutes to storage
        """
        self.logger.info(
            f"Starting minute synchronization "
            f"for legislature {legislature}"
        )
        
        # Step 1: Retrieve all session metadata
        all_sessions = self.session_metadata_repo.retrieve_all_sessions()
        self.logger.info(f"Retrieved {len(all_sessions)} sessions")
        
        # Step 2: Apply business rules to filter sessions
        sessions_to_process = self._filter_sessions_by_business_rules(
            all_sessions
        )
        self.logger.info(
            f"Processing {len(sessions_to_process)} "
            f"sessions after filtering"
        )
        
        if not sessions_to_process:
            self.logger.warning("No sessions to process")
            return
        
        # Step 3: Retrieve full content and create minute entities
        minutes = self._create_minutes_from_sessions(sessions_to_process)
        
        # Step 4: Save all minutes
        if minutes:
            self.minute_repo.save_minutes(minutes)
            self.logger.info(f"Successfully saved {len(minutes)} minutes")
    
    def _filter_sessions_by_business_rules(
        self,
        all_sessions: List[SessionMetadata]
    ) -> List[SessionMetadata]:
        """
        Filter sessions based on business rules.
        
        Rules:
        - Include all provisional sessions (always recalculated)
        - Include only unregistered definitive sessions
        
        Args:
            all_sessions: Complete list of session metadata
            
        Returns:
            Filtered list of sessions to process
        """
        # Separate provisional and definitive sessions
        provisional_sessions = [s for s in all_sessions if s.is_provisional]
        definitive_sessions = [s for s in all_sessions if not s.is_provisional]
        
        self.logger.info(
            f"Found {len(provisional_sessions)} provisional and "
            f"{len(definitive_sessions)} definitive sessions"
        )
        
        # Get existing references for definitive sessions
        if definitive_sessions:
            definitive_refs = [str(s.reference) for s in definitive_sessions]
            existing_refs = self.minute_repo.find_existing_references(definitive_refs)
            
            # Filter out already registered definitive sessions
            unregistered_definitive = [
                s for s in definitive_sessions
                if str(s.reference) not in existing_refs
            ]
            
            self.logger.info(
                f"Found {len(unregistered_definitive)} unregistered definitive sessions"
            )
        else:
            unregistered_definitive = []
        
        # Combine: all provisional + unregistered definitive
        return provisional_sessions + unregistered_definitive
    
    def _create_minutes_from_sessions(
        self,
        sessions: List[SessionMetadata]
    ) -> List[ParliamentaryMinute]:
        """
        Create minute entities by retrieving full content for each session.
        
        Args:
            sessions: List of session metadata
            
        Returns:
            List of complete ParliamentaryMinute entities
        """
        minutes = []
        
        for session in sessions:
            try:
                # Retrieve full content from web
                full_content = self.content_retriever.retrieve_content(
                    session.document_url
                )
                
                # Store content and get storage key
                storage_key = self.content_storage.store_content(
                    str(session.reference),
                    full_content
                )
                
                # Create domain entity with storage key
                minute = ParliamentaryMinute(
                    metadata=session,
                    content_storage_key=storage_key
                )
                
                minutes.append(minute)
                self.logger.debug(f"Created minute for session {session.reference}")
                
            except Exception as e:
                self.logger.error(
                    f"Failed to create minute for session {session.reference}: {e}"
                )
                continue
        
        return minutes
