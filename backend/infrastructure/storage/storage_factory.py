"""
Storage Factory for creating content storage instances.

Provides factory methods to create storage instances based on 
environment configuration with support for content segregation.
"""

import os
import logging
from typing import Optional
from domain.repositories import IContentStorage
from .local_file_storage import LocalFileSystemStorage
from .azure_blob_storage import AzureBlobStorage


class StorageFactory:
    """
    Factory for creating content storage instances.
    
    Supports both local filesystem and Azure blob storage with
    configurable storage segregation for different content types.
    
    Environment Variables:
        CONTENT_STORAGE: 'local' (default) or 'azure'
        LOCAL_STORAGE_PATH: Base path for local storage (default: ./data)
        AZURE_STORAGE_CONNECTION_STRING: Azure connection string
        AZURE_STORAGE_CONTAINER: Azure container name (default: 'parliament')
        
        # Storage segregation (subdirs for local, prefixes for Azure)
        MINUTES_STORAGE_NAME: Storage name for minutes (default: 'minutes')
        CLEANED_STORAGE_NAME: Storage name for cleaned text (default: 'cleaned')
    """
    
    @staticmethod
    def create_storage(
        storage_name: Optional[str] = None,
        storage_type: Optional[str] = None
    ) -> IContentStorage:
        """
        Create a content storage instance with segregation support.
        
        Args:
            storage_name: Name for storage segregation (e.g., 'minutes', 'cleaned').
                         For local: creates subdirectory (data/minutes/, data/cleaned/)
                         For Azure: adds blob prefix (minutes/file.html, cleaned/file.html)
                         If None, uses default based on context.
            storage_type: 'local' or 'azure'. If None, reads from CONTENT_STORAGE env var.
            
        Returns:
            IContentStorage implementation configured for the specified storage name
        """
        logger = logging.getLogger(__name__)
        
        if storage_type is None:
            storage_type = os.getenv('CONTENT_STORAGE', 'local').lower()
        
        if storage_type == 'azure':
            return StorageFactory._create_azure_storage(storage_name, logger)
        else:
            return StorageFactory._create_local_storage(storage_name, logger)
    
    @staticmethod
    def _create_local_storage(
        storage_name: Optional[str],
        logger: logging.Logger
    ) -> LocalFileSystemStorage:
        """Create local filesystem storage with subdirectory segregation."""
        base_path = os.getenv('LOCAL_STORAGE_PATH')
        
        logger.info(
            f"Creating Local File System Storage "
            f"(storage_name: {storage_name or 'default'})"
        )
        
        return LocalFileSystemStorage(
            base_path=base_path,
            storage_name=storage_name
        )
    
    @staticmethod
    def _create_azure_storage(
        storage_name: Optional[str],
        logger: logging.Logger
    ) -> AzureBlobStorage:
        """Create Azure blob storage with prefix segregation."""
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        container_name = os.getenv('AZURE_STORAGE_CONTAINER', 'parliament')
        
        logger.info(
            f"Creating Azure Blob Storage "
            f"(container: {container_name}, storage_name: {storage_name or 'root'})"
        )
        
        return AzureBlobStorage(
            connection_string=connection_string,
            container_name=container_name,
            storage_name=storage_name
        )
    
    @staticmethod
    def create_minutes_storage() -> IContentStorage:
        """
        Create storage for original parliamentary minutes.
        
        Uses MINUTES_STORAGE_NAME env var (default: 'minutes').
        Local: data/minutes/
        Azure: parliament/minutes/
        
        Returns:
            IContentStorage for minutes
        """
        storage_name = os.getenv('MINUTES_STORAGE_NAME', 'minutes')
        return StorageFactory.create_storage(storage_name=storage_name)
    
    @staticmethod
    def create_cleaned_storage() -> IContentStorage:
        """
        Create storage for cleaned text content.
        
        Uses CLEANED_STORAGE_NAME env var (default: 'cleaned').
        Local: data/cleaned/
        Azure: parliament/cleaned/
        
        Returns:
            IContentStorage for cleaned text
        """
        storage_name = os.getenv('CLEANED_STORAGE_NAME', 'cleaned')
        return StorageFactory.create_storage(storage_name=storage_name)
