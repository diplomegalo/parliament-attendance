"""
PostgreSQL minister attendance repository implementation.

Implements minister attendance data persistence using PostgreSQL.
"""

import psycopg2
from typing import List
from psycopg2.extras import execute_batch
from contextlib import contextmanager
import os
from domain.repositories import IMinisterAttendanceRepository
from domain.entities.minister_attendance import MinisterAttendance


class PostgreSQLMinisterAttendanceRepository(
    IMinisterAttendanceRepository
):
    """
    PostgreSQL implementation of minister attendance repository.
    
    Handles CRUD operations for minister attendance records.
    Only tracks attendance for minutes with vote nominatif.
    """
    
    def __init__(self):
        """Initialize repository with database connection."""
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'parliament_attendance'),
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
    
    def save(
        self,
        attendance: MinisterAttendance
    ) -> MinisterAttendance:
        """Save a minister attendance record."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO minister_attendance
                        (minister_id, minute_ref, legislature, present,
                         confidence_score, context)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (minister_id, minute_ref, legislature)
                    DO UPDATE SET
                        present = EXCLUDED.present,
                        confidence_score = EXCLUDED.confidence_score,
                        context = EXCLUDED.context,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                    """,
                    (
                        attendance.minister_id,
                        attendance.minute_ref,
                        attendance.legislature,
                        attendance.present,
                        float(attendance.confidence_score.value)
                        if attendance.confidence_score else None,
                        attendance.context
                    )
                )
                attendance.id = cursor.fetchone()[0]
                conn.commit()
        
        return attendance
    
    def save_batch(
        self,
        attendances: List[MinisterAttendance]
    ) -> List[MinisterAttendance]:
        """Save multiple attendance records in a batch."""
        if not attendances:
            return []
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # Prepare data for batch insert
                data = [
                    (
                        a.minister_id,
                        a.minute_ref,
                        a.legislature,
                        a.present,
                        float(a.confidence_score.value)
                        if a.confidence_score else None,
                        a.context
                    )
                    for a in attendances
                ]
                
                # Execute batch insert
                execute_batch(
                    cursor,
                    """
                    INSERT INTO minister_attendance
                        (minister_id, minute_ref, legislature, present,
                         confidence_score, context)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (minister_id, minute_ref, legislature)
                    DO UPDATE SET
                        present = EXCLUDED.present,
                        confidence_score = EXCLUDED.confidence_score,
                        context = EXCLUDED.context,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    data
                )
                conn.commit()
        
        return attendances
    
    def find_by_minute(
        self,
        minute_ref: str,
        legislature: int
    ) -> List[MinisterAttendance]:
        """Find all minister attendance records for a minute."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, minister_id, minute_ref, legislature,
                           present, confidence_score, context
                    FROM minister_attendance
                    WHERE minute_ref = %s AND legislature = %s
                    ORDER BY minister_id
                    """,
                    (minute_ref, legislature)
                )
                
                rows = cursor.fetchall()
                return [
                    MinisterAttendance(
                        id=row[0],
                        minister_id=row[1],
                        minute_ref=row[2],
                        legislature=row[3],
                        present=row[4],
                        confidence_score=row[5],
                        context=row[6]
                    )
                    for row in rows
                ]
    
    def find_by_minister(
        self,
        minister_id: str,
        legislature: int
    ) -> List[MinisterAttendance]:
        """Find all attendance records for a minister."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, minister_id, minute_ref, legislature,
                           present, confidence_score, context
                    FROM minister_attendance
                    WHERE minister_id = %s AND legislature = %s
                    ORDER BY minute_ref
                    """,
                    (minister_id, legislature)
                )
                
                rows = cursor.fetchall()
                return [
                    MinisterAttendance(
                        id=row[0],
                        minister_id=row[1],
                        minute_ref=row[2],
                        legislature=row[3],
                        present=row[4],
                        confidence_score=row[5],
                        context=row[6]
                    )
                    for row in rows
                ]
    
    def delete_by_minute(
        self,
        minute_ref: str,
        legislature: int
    ) -> int:
        """Delete all minister attendance records for a minute."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM minister_attendance
                    WHERE minute_ref = %s AND legislature = %s
                    """,
                    (minute_ref, legislature)
                )
                deleted_count = cursor.rowcount
                conn.commit()
        
        return deleted_count
    
    def get_attendance_summary(
        self,
        minister_id: str,
        legislature: int
    ) -> dict:
        """Get attendance summary statistics for a minister."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) as total_minutes,
                        SUM(CASE WHEN present THEN 1 ELSE 0 END)
                            as present_count,
                        SUM(CASE WHEN NOT present THEN 1 ELSE 0 END)
                            as absent_count
                    FROM minister_attendance
                    WHERE minister_id = %s AND legislature = %s
                    """,
                    (minister_id, legislature)
                )
                
                row = cursor.fetchone()
                total = row[0] or 0
                present = row[1] or 0
                absent = row[2] or 0
                
                attendance_rate = (
                    (present / total * 100) if total > 0 else 0.0
                )
                
                return {
                    'total_minutes': total,
                    'present_count': present,
                    'absent_count': absent,
                    'attendance_rate': round(attendance_rate, 2)
                }
