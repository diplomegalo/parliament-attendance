"""
Session Metadata Repository interface.

Defines how to retrieve session metadata from external sources.
"""

from abc import ABC, abstractmethod
from typing import List

from domain.entities.session_metadata import SessionMetadata


class ISessionMetadataRepository(ABC):
    """
    Repository interface for retrieving session metadata.
    
    This port defines how to fetch session information from external sources
    without coupling to specific implementation details.
    """
    
    @abstractmethod
    def retrieve_all_sessions(self) -> List[SessionMetadata]:
        """
        Retrieve metadata for all available parliamentary sessions.
        
        Returns:
            List of SessionMetadata objects
        """
        pass
