"""
Use case: Synchronize Parliament Members.

This use case ensures member data exists for a specific legislature
before processing minutes.
"""

import logging
from domain.repositories import IMemberRepository, IMemberScraper


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
