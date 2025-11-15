"""
Database repository implementation for parliamentary minutes.

This infrastructure adapter implements the minute repository interface
using PostgreSQL database operations.
"""

import os
import psycopg2
import logging
from typing import List, Set
from contextlib import contextmanager

from domain.entities import ParliamentaryMinute
from domain.repositories import IMinuteRepository


class PostgresMinuteRepository(IMinuteRepository):
    """
    PostgreSQL implementation of minute repository.
    
    Handles persistence of parliamentary minutes using PostgreSQL database.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'db'),
            'dbname': os.getenv('DB_NAME', 'parliament_attendance'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'port': os.getenv('DB_PORT', 5432)
        }
    
    @contextmanager
    def _get_cursor(self):
        """Context manager for database operations."""
        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def save_minutes(self, minutes: List[ParliamentaryMinute]) -> None:
        """
        Save multiple minutes to PostgreSQL database.
        
        Stores only metadata and content storage key reference.
        Large content is stored separately via IContentStorage.
        
        Uses bulk insert with ON CONFLICT to handle updates.
        
        Args:
            minutes: List of ParliamentaryMinute entities
        """
        if not minutes:
            return
        
        with self._get_cursor() as cursor:
            # Prepare metadata for bulk insert
            metadata_data = [
                (
                    minute.get_reference(),
                    minute.metadata.date.isoformat(),
                    minute.metadata.description,
                    minute.metadata.document_url,
                    minute.metadata.is_provisional,
                    minute.content_storage_key,
                    minute.metadata.legislature,
                )
                for minute in minutes
            ]
            
            # Insert/update metadata with content storage key
            cursor.executemany("""
                INSERT INTO minutes (
                    ref,
                    date,
                    session,
                    url,
                    is_temporary,
                    content_storage_key,
                    legislature
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ref) DO UPDATE SET
                    date = EXCLUDED.date,
                    session = EXCLUDED.session,
                    url = EXCLUDED.url,
                    is_temporary = EXCLUDED.is_temporary,
                    content_storage_key = EXCLUDED.content_storage_key,
                    legislature = EXCLUDED.legislature,
                    updated_at = CURRENT_TIMESTAMP
            """, metadata_data)
            
            self.logger.info(f"Saved {len(minutes)} minutes to database")
    
    def find_existing_references(self, references: List[str]) -> Set[str]:
        """
        Find which session references exist in the database.
        
        Args:
            references: List of reference strings to check
            
        Returns:
            Set of references that exist in database
        """
        if not references:
            return set()
        
        with self._get_cursor() as cursor:
            placeholders = ",".join(["%s"] * len(references))
            query = f"SELECT ref FROM minutes WHERE ref IN ({placeholders})"
            cursor.execute(query, references)
            
            existing = {row[0] for row in cursor.fetchall()}
            self.logger.debug(f"Found {len(existing)} existing references")
            return existing
