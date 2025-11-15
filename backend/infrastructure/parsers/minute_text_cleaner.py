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
        Filter HTML to include only voting sections.
        
        Searches for the earliest occurrence of vote-related markers:
        - "Stemming/vote N" (vote results)
        - "Naamstemming - Vote nominatif: N" (nominal votes)
        - "DETAIL VAN DE NAAMSTEMMINGEN" (Dutch detail section)
        - "DETAIL DES VOTES NOMINATIFS" (French detail section)
        
        Returns all HTML content from that point onward, preserving:
        - Vote titles and numbers
        - Voting process text
        - Vote results tables
        - Member name lists
        - Both Dutch and French bilingual content
        
        Args:
            html_content: Raw HTML from parliamentary minute
            
        Returns:
            Filtered HTML containing only voting sections,
            or None if no voting markers found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Vote marker patterns (case-insensitive, flexible spacing)
        vote_patterns = [
            re.compile(r'Stemming/vote\s+\d+', re.IGNORECASE),
            re.compile(r'Naamstemming.*Vote nominatif', re.IGNORECASE),
            re.compile(r'DETAIL VAN DE NAAMSTEMMINGEN', re.IGNORECASE),
            re.compile(r'DETAIL DES VOTES NOMINATIFS', re.IGNORECASE)
        ]
        
        # Find all elements that could contain vote markers
        all_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'])
        
        # Search for the first occurrence of any vote marker
        first_vote_element = None
        for element in all_elements:
            text = element.get_text(strip=True)
            for pattern in vote_patterns:
                if pattern.search(text):
                    first_vote_element = element
                    break
            if first_vote_element:
                break
        
        # No voting sections found
        if not first_vote_element:
            return None
        
        # Create new soup with filtered content
        # Extract all siblings after (and including) the first vote element
        filtered_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        body = filtered_soup.body
        
        # Add the first vote element and all following siblings
        current = first_vote_element
        while current:
            # Clone and append the element
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
