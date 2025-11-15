"""
PostgreSQL attendance repository implementation.

Implements attendance data persistence using PostgreSQL.
"""

import psycopg2
from typing import List, Optional
from psycopg2.extras import execute_batch
from domain.repositories import IAttendanceRepository
from domain.entities import MemberPresence


class PostgreSQLAttendanceRepository(IAttendanceRepository):
    """
    PostgreSQL implementation of attendance repository.
    
    Handles CRUD operations for member presence records.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize repository with database connection.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
    
    def save(self, presence: MemberPresence) -> MemberPresence:
        """Save a member presence record."""
        with psycopg2.connect(self.connection_string) as conn:
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
        
        with psycopg2.connect(self.connection_string) as conn:
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
        with psycopg2.connect(self.connection_string) as conn:
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
        with psycopg2.connect(self.connection_string) as conn:
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
        with psycopg2.connect(self.connection_string) as conn:
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
