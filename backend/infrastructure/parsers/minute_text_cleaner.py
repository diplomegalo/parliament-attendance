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
    
    def extract_text(
        self,
        html_content: str,
        extract_votes_only: bool = False
    ) -> Optional[str]:
        """
        Extract clean text from HTML minute content.
        
        Args:
            html_content: Raw HTML from parliamentary minute
            extract_votes_only: If True, extract only voting sections.
                               Returns None if no votes found.
            
        Returns:
            Clean text suitable for AI processing, or None if
            extract_votes_only=True and no voting sections found
            
        Raises:
            ValueError: If html_content is empty or invalid
        """
        if not html_content or not html_content.strip():
            raise ValueError("HTML content cannot be empty")
        
        # Filter to voting sections if requested
        if extract_votes_only:
            filtered_html = self._filter_to_voting_sections(html_content)
            if filtered_html is None:
                return None
            html_content = filtered_html
        
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
    
    def _filter_to_voting_sections(self, html_content: str) -> Optional[str]:
        """
        Filter HTML to extract only vote nominatif and DETAIL sections.
        
        Two-phase extraction:
        1. Vote nominatif: Individual vote results with "(Stemming/vote N)"
        2. DETAIL section: Member names organized by vote number
        
        Searches for markers:
        - "(Stemming/vote N)" - vote results with topics
        - "DETAIL VAN DE NAAMSTEMMINGEN" / "DETAIL DES VOTES NOMINATIFS"
        
        Args:
            html_content: Raw HTML from parliamentary minute
            
        Returns:
            Filtered HTML with vote topics and member details,
            or None if no voting markers found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Patterns for vote sections
        stemming_pattern = re.compile(
            r'\(Stemming/vote\s+\d+\)',
            re.IGNORECASE
        )
        detail_pattern = re.compile(
            r'DETAIL (VAN DE NAAMSTEMMINGEN|DES VOTES NOMINATIFS)',
            re.IGNORECASE
        )
        
        # Find the first element containing a vote marker
        first_vote_element = None
        detail_element = None
        
        # Search through all elements in document order
        for element in soup.find_all(['p', 'h1', 'h2', 'table']):
            text = element.get_text()
            
            # Check for first vote
            if first_vote_element is None and stemming_pattern.search(text):
                first_vote_element = element
            
            # Check for DETAIL section
            if detail_element is None and detail_pattern.search(text):
                detail_element = element
            
            # Stop if we found both
            if first_vote_element and detail_element:
                break
        
        # No votes found
        if first_vote_element is None and detail_element is None:
            return None
        
        # Create filtered soup
        filtered_soup = BeautifulSoup(
            '<html><body></body></html>',
            'html.parser'
        )
        body = filtered_soup.body
        
        # Start from whichever comes first
        start_element = first_vote_element or detail_element
        
        # Add the starting element and all its following siblings
        current = start_element
        while current:
            body.append(current.__copy__())
            current = current.find_next_sibling()
        
        # If DETAIL is in a different parent, add it too
        if detail_element and detail_element != start_element:
            # Check if detail_element is already included
            if not filtered_soup.find(text=detail_pattern):
                # DETAIL is in a different section, add it
                current = detail_element
                while current:
                    body.append(current.__copy__())
                    current = current.find_next_sibling()
        
        return str(filtered_soup)
    
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
