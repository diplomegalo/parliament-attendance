"""
PostgreSQL attendance repository implementation.

Implements attendance data persistence using PostgreSQL.
"""

import psycopg2
from typing import List, Optional
from psycopg2.extras import execute_batch
from contextlib import contextmanager
import os
from domain.repositories import IAttendanceRepository
from domain.entities import MemberPresence


class PostgreSQLAttendanceRepository(IAttendanceRepository):
    """
    PostgreSQL implementation of attendance repository.
    
    Handles CRUD operations for member presence records.
    """
    
    def __init__(self):
        """
        Initialize repository with database connection from environment.
        """
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'parliament'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = psycopg2.connect(**self.connection_params)
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def save(self, presence: MemberPresence) -> MemberPresence:
        """Save a member presence record."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO attendance
                        (member_id, session_ref, legislature, spoke,
                         interventions_count, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (member_id, session_ref)
                    DO UPDATE SET
                        spoke = EXCLUDED.spoke,
                        interventions_count = EXCLUDED.interventions_count,
                        confidence_score = EXCLUDED.confidence_score,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                    """,
                    (
                        presence.member_id,
                        presence.session_ref,
                        presence.legislature,
                        presence.spoke,
                        presence.interventions_count,
                        presence.confidence_score
                    )
                )
                presence.id = cursor.fetchone()[0]
                conn.commit()
        
        return presence
    
    def save_batch(
        self,
        presences: List[MemberPresence]
    ) -> List[MemberPresence]:
        """Save multiple presence records in a batch."""
        if not presences:
            return []
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # Prepare data for batch insert
                data = [
                    (
                        p.member_id,
                        p.session_ref,
                        p.legislature,
                        p.spoke,
                        p.interventions_count,
                        p.confidence_score
                    )
                    for p in presences
                ]
                
                execute_batch(
                    cursor,
                    """
                    INSERT INTO attendance
                        (member_id, session_ref, legislature, spoke,
                         interventions_count, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (member_id, session_ref)
                    DO UPDATE SET
                        spoke = EXCLUDED.spoke,
                        interventions_count = EXCLUDED.interventions_count,
                        confidence_score = EXCLUDED.confidence_score,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    data
                )
                
                # Fetch all IDs for the session
                cursor.execute(
                    """
                    SELECT id, member_id
                    FROM attendance
                    WHERE session_ref = %s
                    """,
                    (presences[0].session_ref,)
                )
                
                id_map = {row[1]: row[0] for row in cursor.fetchall()}
                
                # Set IDs on presence objects
                for p in presences:
                    p.id = id_map.get(p.member_id)
                
                conn.commit()
        
        return presences
    
    def find_by_session(
        self,
        session_ref: str,
        legislature: Optional[int] = None
    ) -> List[MemberPresence]:
        """Find all attendance records for a session."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                if legislature is not None:
                    cursor.execute(
                        """
                        SELECT id, member_id, session_ref, legislature,
                               spoke, interventions_count, confidence_score
                        FROM attendance
                        WHERE session_ref = %s AND legislature = %s
                        ORDER BY member_id
                        """,
                        (session_ref, legislature)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, member_id, session_ref, legislature,
                               spoke, interventions_count, confidence_score
                        FROM attendance
                        WHERE session_ref = %s
                        ORDER BY member_id
                        """,
                        (session_ref,)
                    )
                
                return [
                    MemberPresence(
                        member_id=row[1],
                        session_ref=row[2],
                        legislature=row[3],
                        spoke=row[4],
                        interventions_count=row[5],
                        confidence_score=row[6],
                        id=row[0]
                    )
                    for row in cursor.fetchall()
                ]
    
    def find_by_member(
        self,
        member_id: str,
        legislature: int
    ) -> List[MemberPresence]:
        """Find all attendance records for a member."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, member_id, session_ref, legislature,
                           spoke, interventions_count, confidence_score
                    FROM attendance
                    WHERE member_id = %s AND legislature = %s
                    ORDER BY session_ref
                    """,
                    (member_id, legislature)
                )
                
                return [
                    MemberPresence(
                        member_id=row[1],
                        session_ref=row[2],
                        legislature=row[3],
                        spoke=row[4],
                        interventions_count=row[5],
                        confidence_score=row[6],
                        id=row[0]
                    )
                    for row in cursor.fetchall()
                ]
    
    def delete_by_session(self, session_ref: str) -> int:
        """Delete all attendance records for a session."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM attendance
                    WHERE session_ref = %s
                    """,
                    (session_ref,)
                )
                deleted = cursor.rowcount
                conn.commit()
        
        return deleted
    
    def save_batch_from_dicts(
        self,
        attendance_dicts: List[dict],
        legislature: int
    ) -> int:
        """
        Save attendance records from parser dict format.
        
        Args:
            attendance_dicts: List of dicts from LLM parser with keys:
                             member_id, session_ref, spoke, confidence
            legislature: Legislature number to add to records
            
        Returns:
            Number of records saved
        """
        if not attendance_dicts:
            return 0
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # Prepare data for batch insert
                data = [
                    (
                        att['member_id'],
                        att['session_ref'],
                        legislature,
                        att['spoke'],
                        1 if att['spoke'] else 0,  # interventions_count
                        att['confidence']
                    )
                    for att in attendance_dicts
                ]
                
                execute_batch(
                    cursor,
                    """
                    INSERT INTO attendance
                        (member_id, session_ref, legislature, spoke,
                         interventions_count, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (member_id, session_ref)
                    DO UPDATE SET
                        spoke = EXCLUDED.spoke,
                        interventions_count = EXCLUDED.interventions_count,
                        confidence_score = EXCLUDED.confidence_score,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    data
                )
                conn.commit()
        
        return len(attendance_dicts)
