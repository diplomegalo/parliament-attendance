"""
Azure Blob Storage implementation for minute content.

This infrastructure adapter stores content files in Azure Blob Storage,
suitable for production environments.
"""

import logging
from domain.repositories import IContentStorage

try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class AzureBlobStorage(IContentStorage):
    """
    Store content in Azure Blob Storage.
    
    Stores HTML/text files as blobs in Azure Storage.
    Suitable for production and cloud-hosted environments.
    """
    
    def __init__(self, connection_string: str = None, container_name: str = "minutes"):
        """
        Initialize Azure Blob Storage.
        
        Args:
            connection_string: Azure Storage connection string.
                              If None, reads from AZURE_STORAGE_CONNECTION_STRING env var
            container_name: Name of the blob container to use
            
        Raises:
            ImportError: If azure-storage-blob is not installed
            ValueError: If connection string is not provided
        """
        if not AZURE_AVAILABLE:
            raise ImportError(
                "azure-storage-blob is required for Azure Blob Storage. "
                "Install it with: pip install azure-storage-blob"
            )
        
        import os
        if connection_string is None:
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        
        if not connection_string:
            raise ValueError(
                "Azure Storage connection string must be provided either as "
                "parameter or via AZURE_STORAGE_CONNECTION_STRING environment variable"
            )
        
        self.logger = logging.getLogger(__name__)
        self.container_name = container_name
        
        # Initialize blob service client
        self.blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service.get_container_client(container_name)
        
        # Create container if it doesn't exist
        try:
            self.container_client.create_container()
            self.logger.info(f"Created blob container: {container_name}")
        except Exception as e:
            # Container already exists or other error
            self.logger.debug(f"Container status: {str(e)}")
        
        self.logger.info(f"Initialized Azure Blob Storage: container={container_name}")
    
    def store_content(self, reference: str, content: str) -> str:
        """
        Store content as blob in Azure Storage.
        
        Args:
            reference: Session reference identifier
            content: Full text content to store
            
        Returns:
            Blob name as storage key
        """
        # Sanitize blob name - replace problematic characters
        blob_name = reference.replace('/', '_').replace('\\', '_').replace(' ', '_')
        blob_name = f"{blob_name}.html"
        
        # Get blob client and upload
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.upload_blob(content, overwrite=True)
        
        self.logger.debug(f"Stored blob: {blob_name} ({len(content)} bytes)")
        
        # Return blob name as storage key
        return blob_name
    
    def retrieve_content(self, storage_key: str) -> str:
        """
        Retrieve content from Azure blob.
        
        Args:
            storage_key: Blob name returned by store_content
            
        Returns:
            The stored content
            
        Raises:
            Exception: If blob doesn't exist or retrieval fails
        """
        blob_client = self.container_client.get_blob_client(storage_key)
        content = blob_client.download_blob().readall().decode('utf-8')
        
        self.logger.debug(f"Retrieved blob: {storage_key}")
        return content
    
    def exists(self, storage_key: str) -> bool:
        """
        Check if blob exists.
        
        Args:
            storage_key: Blob name to check
            
        Returns:
            True if blob exists, False otherwise
        """
        blob_client = self.container_client.get_blob_client(storage_key)
        return blob_client.exists()
