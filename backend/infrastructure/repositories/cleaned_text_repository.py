"""
PostgreSQL cleaned text repository implementation.

Stores metadata in database only (content handled by use case).
"""

import os
import psycopg2
import logging
from typing import Optional
from contextlib import contextmanager
from domain.repositories import ICleanedTextRepository
from domain.entities import CleanedMinuteText


class PostgreSQLCleanedTextRepository(ICleanedTextRepository):
    """
    PostgreSQL implementation for cleaned text metadata.
    
    Stores only metadata in database. Content storage is handled
    by the use case (same pattern as SynchronizeMinutesUseCase).
    """
    
    def __init__(self):
        """Initialize repository with database connection."""
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
    
    def save_metadata(self, metadata: CleanedMinuteText) -> CleanedMinuteText:
        """
        Save cleaned text metadata to database.
        
        Uses ON CONFLICT to update if minute_ref already exists.
        """
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cleaned_texts (
                    minute_ref,
                    content_storage_key,
                    cleaning_method,
                    text_hash
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (minute_ref) DO UPDATE SET
                    content_storage_key = EXCLUDED.content_storage_key,
                    cleaning_method = EXCLUDED.cleaning_method,
                    text_hash = EXCLUDED.text_hash,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, created_at, updated_at
                """,
                (
                    metadata.minute_ref,
                    metadata.content_storage_key,
                    metadata.cleaning_method,
                    metadata.text_hash
                )
            )
            
            row = cursor.fetchone()
            metadata_id, created_at, updated_at = row
        
        # Update entity with database values
        metadata.id = metadata_id
        metadata.created_at = created_at
        metadata.updated_at = updated_at
        
        self.logger.info(
            f"Saved cleaned text metadata for {metadata.minute_ref} "
            f"(hash: {metadata.text_hash[:8]}...)"
        )
        
        return metadata
    
    def find_by_minute_ref(
        self,
        minute_ref: str
    ) -> Optional[CleanedMinuteText]:
        """Find metadata from database."""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, minute_ref, content_storage_key,
                       cleaning_method, text_hash, created_at, updated_at
                FROM cleaned_texts
                WHERE minute_ref = %s
                """,
                (minute_ref,)
            )
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return CleanedMinuteText(
                minute_ref=row[1],
                content_storage_key=row[2],
                cleaning_method=row[3],
                text_hash=row[4],
                created_at=row[5],
                updated_at=row[6],
                id=row[0]
            )
    
    def exists(self, minute_ref: str) -> bool:
        """Check if cleaned text metadata exists in database."""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM cleaned_texts
                WHERE minute_ref = %s
                """,
                (minute_ref,)
            )
            count = cursor.fetchone()[0]
            return count > 0

