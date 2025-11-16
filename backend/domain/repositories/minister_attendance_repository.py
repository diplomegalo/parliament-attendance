"""
Minister Attendance repository interface.

Defines contract for persisting minister attendance data.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.minister_attendance import MinisterAttendance


class IMinisterAttendanceRepository(ABC):
    """
    Interface for managing minister attendance data persistence.
    
    Handles CRUD operations for minister attendance records.
    Only tracks attendance for minutes with vote nominatif.
    """
    
    @abstractmethod
    def save(
        self,
        attendance: MinisterAttendance
    ) -> MinisterAttendance:
        """
        Save a minister attendance record.
        
        Args:
            attendance: MinisterAttendance entity to save
            
        Returns:
            Saved MinisterAttendance with id set
            
        Raises:
            ValueError: If attendance data is invalid
        """
        pass
    
    @abstractmethod
    def save_batch(
        self,
        attendances: List[MinisterAttendance]
    ) -> List[MinisterAttendance]:
        """
        Save multiple attendance records in a batch.
        
        More efficient than multiple save() calls for bulk operations.
        
        Args:
            attendances: List of MinisterAttendance entities to save
            
        Returns:
            List of saved MinisterAttendance entities with ids set
            
        Raises:
            ValueError: If any attendance data is invalid
        """
        pass
    
    @abstractmethod
    def find_by_minute(
        self,
        minute_ref: str,
        legislature: int
    ) -> List[MinisterAttendance]:
        """
        Find all minister attendance records for a minute.
        
        Args:
            minute_ref: Minute reference (e.g., "0072")
            legislature: Legislature number
            
        Returns:
            List of MinisterAttendance entities for the minute
        """
        pass
    
    @abstractmethod
    def find_by_minister(
        self,
        minister_id: str,
        legislature: int
    ) -> List[MinisterAttendance]:
        """
        Find all attendance records for a minister.
        
        Args:
            minister_id: Minister identifier
            legislature: Legislature number
            
        Returns:
            List of MinisterAttendance entities for the minister
        """
        pass
    
    @abstractmethod
    def delete_by_minute(
        self,
        minute_ref: str,
        legislature: int
    ) -> int:
        """
        Delete all minister attendance records for a minute.
        
        Useful for re-processing a minute.
        
        Args:
            minute_ref: Minute reference (e.g., "0072")
            legislature: Legislature number
            
        Returns:
            Number of records deleted
        """
        pass
    
    @abstractmethod
    def get_attendance_summary(
        self,
        minister_id: str,
        legislature: int
    ) -> dict:
        """
        Get attendance summary statistics for a minister.
        
        Args:
            minister_id: Minister identifier
            legislature: Legislature number
            
        Returns:
            Dictionary with keys:
                - total_minutes: Total minutes with votes processed
                - present_count: Number of times present
                - absent_count: Number of times absent
                - attendance_rate: Percentage present (0-100)
        """
        pass
