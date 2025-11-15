"""
Minute text cleaner infrastructure.

Extracts clean text from HTML parliamentary minutes for AI processing.
"""

from bs4 import BeautifulSoup
from typing import Optional
import re


class MinuteTextCleaner:
    """
    Cleans and extracts text from HTML parliamentary minutes.
    
    Removes HTML tags, navigation elements, and formatting while
    preserving the essential content structure for AI parsing.
    """
    
    def extract_text(self, html_content: str) -> str:
        """
        Extract clean text from HTML minute content.
        
        Args:
            html_content: Raw HTML from parliamentary minute
            
        Returns:
            Clean text suitable for AI processing
            
        Raises:
            ValueError: If html_content is empty or invalid
        """
        if not html_content or not html_content.strip():
            raise ValueError("HTML content cannot be empty")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'meta', 'link']):
            element.decompose()
        
        # Remove navigation and header elements
        for element in soup.find_all(['nav', 'header', 'footer']):
            element.decompose()
        
        # Remove elements with common navigation classes/ids
        nav_selectors = [
            'nav', 'navigation', 'menu', 'sidebar',
            'breadcrumb', 'pagination'
        ]
        for selector in nav_selectors:
            for element in soup.find_all(class_=re.compile(selector, re.I)):
                element.decompose()
            for element in soup.find_all(id=re.compile(selector, re.I)):
                element.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        text = self._normalize_whitespace(text)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        - Replace multiple spaces with single space
        - Replace multiple newlines with double newline (paragraph separation)
        - Strip leading/trailing whitespace from lines
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Split into lines and strip each
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines but preserve paragraph breaks
        cleaned_lines = []
        previous_empty = False
        
        for line in lines:
            if line:
                cleaned_lines.append(line)
                previous_empty = False
            elif not previous_empty and cleaned_lines:
                # Keep one empty line for paragraph break
                cleaned_lines.append('')
                previous_empty = True
        
        # Join with newlines
        text = '\n'.join(cleaned_lines)
        
        # Normalize spaces within lines
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def extract_main_content(
        self,
        html_content: str,
        content_selector: Optional[str] = None
    ) -> str:
        """
        Extract main content area from HTML minute.
        
        Optionally use CSS selector to find main content container.
        Falls back to full text extraction if selector not found.
        
        Args:
            html_content: Raw HTML from parliamentary minute
            content_selector: CSS selector for main content (optional)
            
        Returns:
            Clean text from main content area
        """
        if not html_content or not html_content.strip():
            raise ValueError("HTML content cannot be empty")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find main content area
        main_content = None
        
        if content_selector:
            main_content = soup.select_one(content_selector)
        
        # Fallback to common content selectors
        if not main_content:
            for selector in ['main', 'article', '#content', '.content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
        
        # Use full document if no main content found
        if not main_content:
            main_content = soup
        
        # Extract text from main content
        return self.extract_text(str(main_content))
