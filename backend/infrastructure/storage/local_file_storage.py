"""
Local filesystem storage implementation for minute content.

This infrastructure adapter stores content files on the local disk,
suitable for development environments.
"""

import os
import logging
from pathlib import Path
from domain.repositories import IContentStorage


class LocalFileSystemStorage(IContentStorage):
    """
    Store content on local filesystem.
    
    Stores HTML/text files in a local directory structure.
    Suitable for development and testing environments.
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize local file system storage.
        
        Args:
            base_path: Base directory for storing files. 
                      Defaults to ./data/minutes
        """
        if base_path is None:
            base_path = os.getenv('LOCAL_STORAGE_PATH', './data/minutes')
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Initialized local storage at: {self.base_path.absolute()}")
    
    def store_content(self, reference: str, content: str) -> str:
        """
        Store content as HTML file on local filesystem.
        
        Args:
            reference: Session reference identifier
            content: Full text content to store
            
        Returns:
            Relative file path as storage key
        """
        # Sanitize filename - replace problematic characters
        filename = reference.replace('/', '_').replace('\\', '_').replace(' ', '_')
        filename = f"{filename}.html"
        
        filepath = self.base_path / filename
        
        # Write content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.debug(f"Stored content: {filename} ({len(content)} bytes)")
        
        # Return relative path as storage key
        return str(filepath)
    
    def retrieve_content(self, storage_key: str) -> str:
        """
        Retrieve content from local file.
        
        Args:
            storage_key: File path returned by store_content
            
        Returns:
            The stored content
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        with open(storage_key, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.logger.debug(f"Retrieved content: {storage_key}")
        return content
    
    def exists(self, storage_key: str) -> bool:
        """
        Check if file exists.
        
        Args:
            storage_key: File path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return Path(storage_key).exists()
