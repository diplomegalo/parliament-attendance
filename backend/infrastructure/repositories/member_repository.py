"""
Database repository implementation for parliament members.

This infrastructure adapter implements the member repository interface
using PostgreSQL database operations.
"""

import os
import psycopg2
import logging
from typing import List
from contextlib import contextmanager

from domain.repositories import IMemberRepository


class PostgresMemberRepository(IMemberRepository):
    """
    PostgreSQL implementation of member repository.
    
    Handles persistence of parliament members using PostgreSQL database.
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
    
    def has_members_for_legislature(self, legislature: int) -> bool:
        """
        Check if members exist for a specific legislature.
        
        Args:
            legislature: Legislature number to check
            
        Returns:
            True if members exist, False otherwise
        """
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM members WHERE legislature = %s",
                (legislature,)
            )
            count = cursor.fetchone()[0]
            has_members = count > 0
            
            self.logger.debug(
                f"Legislature {legislature}: "
                f"{'has' if has_members else 'no'} members "
                f"({count} found)"
            )
            
            return has_members
    
    def count_members_for_legislature(self, legislature: int) -> int:
        """
        Count members for a specific legislature.
        
        Args:
            legislature: Legislature number
            
        Returns:
            Number of members for that legislature
        """
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM members WHERE legislature = %s",
                (legislature,)
            )
            count = cursor.fetchone()[0]
            
            self.logger.debug(
                f"Legislature {legislature}: {count} members"
            )
            
            return count
    
    def save_members(self, members: List) -> None:
        """
        Save multiple members to PostgreSQL database.
        
        Uses bulk insert with ON CONFLICT to handle updates.
        
        Args:
            members: List of ParliamentMember entities
        """
        if not members:
            return
        
        with self._get_cursor() as cursor:
            # Prepare member data for bulk insert
            member_data = [
                (
                    member.member_id,
                    member.legislature,
                    member.full_name,
                    member.last_name,
                    member.first_name,
                )
                for member in members
            ]
            
            # Insert/update members
            cursor.executemany("""
                INSERT INTO members (
                    member_id,
                    legislature,
                    full_name,
                    last_name,
                    first_name
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (member_id, legislature) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    last_name = EXCLUDED.last_name,
                    first_name = EXCLUDED.first_name,
                    updated_at = CURRENT_TIMESTAMP
            """, member_data)
            
            self.logger.info(
                f"Saved {len(members)} members to database "
                f"(legislature {members[0].legislature if members else 'N/A'})"
            )
    
    def find_by_legislature(self, legislature: int) -> List:
        """
        Find all members for a specific legislature.
        
        Args:
            legislature: Legislature number
            
        Returns:
            List of member dictionaries with id, member_id, legislature,
            full_name, last_name, first_name
        """
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT id, member_id, legislature, full_name,
                       last_name, first_name, created_at, updated_at
                FROM members
                WHERE legislature = %s
                ORDER BY last_name, first_name
            """, (legislature,))
            
            rows = cursor.fetchall()
            
            members = [
                {
                    'id': row[0],
                    'member_id': row[1],
                    'legislature': row[2],
                    'full_name': row[3],
                    'last_name': row[4],
                    'first_name': row[5],
                    'created_at': row[6],
                    'updated_at': row[7],
                }
                for row in rows
            ]
            
            self.logger.debug(
                f"Found {len(members)} members for legislature {legislature}"
            )
            
            return members
