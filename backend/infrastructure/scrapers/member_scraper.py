"""
Infrastructure: Belgian Chamber member scraper.

Retrieves official list of parliament members from lachambre.be
for name validation and metadata enrichment.
"""

import logging
import re
from typing import List, Optional
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup


@dataclass
class ParliamentMember:
    """
    Domain entity representing a parliament member.
    
    A member can serve in multiple legislatures. The member_id is permanent
    across legislatures (from the Chamber website key parameter).
    
    Attributes:
        member_id: Unique identifier from Chamber website
                  (persists across legislatures)
        full_name: Complete name (LastName FirstName)
        last_name: Family name
        first_name: Given name(s)
        legislature: Legislature number (e.g., 56)
    """
    member_id: str
    full_name: str
    last_name: str
    first_name: str
    legislature: int
    
    def __post_init__(self):
        """Normalize name formatting and validate."""
        # Ensure consistent spacing
        self.full_name = ' '.join(self.full_name.split())
        self.last_name = ' '.join(self.last_name.split())
        self.first_name = ' '.join(self.first_name.split())
        
        # Validate legislature
        if self.legislature < 1:
            raise ValueError("Legislature must be a positive integer")


class ChamberMemberScraper:
    """
    Scrapes member list from Belgian Chamber of Representatives.
    
    Retrieves official member data from:
    https://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&cfm=cvlist54.cfm?legis=56
    
    Handles CAPTCHA protection by requiring manual HTML download or
    using session cookies.
    """
    
    BASE_URL = "https://www.lachambre.be"
    MEMBER_LIST_URL = (
        "{base}/kvvcr/showpage.cfm?"
        "section=/depute&language=fr&cfm=cvlist54.cfm?"
        "legis={legislature}&today=n"
    )
    
    def __init__(self, session: Optional[requests.Session] = None):
        """
        Initialize scraper.
        
        Args:
            session: Optional requests.Session with cookies/headers
                    for bypassing bot protection
        """
        self.logger = logging.getLogger(__name__)
        self.session = session or requests.Session()
        
        # Set browser-like headers
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Referer': 'https://www.lachambre.be/'
        })
    
    def scrape_members(
        self,
        legislature: int = 56,
        html_content: Optional[str] = None
    ) -> List[ParliamentMember]:
        """
        Scrape member list for a legislature.
        
        Args:
            legislature: Legislature number (default 56)
            html_content: Optional pre-downloaded HTML content
                         (use when site has bot protection)
        
        Returns:
            List of ParliamentMember objects
        
        Raises:
            ValueError: If HTML structure doesn't match expected format
            requests.RequestException: If download fails
        """
        if html_content:
            self.logger.info(
                f"Parsing members from provided HTML "
                f"(legislature {legislature})"
            )
            soup = BeautifulSoup(html_content, 'html.parser')
        else:
            url = self.MEMBER_LIST_URL.format(
                base=self.BASE_URL,
                legislature=legislature
            )
            self.logger.info(f"Fetching members from: {url}")
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch member list: {e}")
                raise
        
        # Parse HTML table
        members = self._parse_member_table(soup, legislature)
        
        self.logger.info(
            f"Successfully scraped {len(members)} members "
            f"for legislature {legislature}"
        )
        
        return members
    
    def _parse_member_table(
        self,
        soup: BeautifulSoup,
        legislature: int
    ) -> List[ParliamentMember]:
        """
        Parse member table from HTML.
        
        Expected structure:
        <table>
          <tr>
            <td><a href="...key=XXX">LastName FirstName</a></td>
          </tr>
        </table>
        """
        members = []
        
        # Find main member table
        # Usually has class or is the largest table
        tables = soup.find_all('table')
        
        if not tables:
            raise ValueError("No tables found in HTML")
        
        # Try each table until we find one with member data
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) < 3:
                    continue
                
                # First cell should contain member link
                link = cells[0].find('a')
                if not link:
                    continue
                
                # Extract member ID from link
                href = link.get('href', '')
                if not href:
                    continue
                member_id = self._extract_member_id(str(href))
                
                if not member_id:
                    continue
                
                # Extract name
                full_name = link.get_text(strip=True)
                
                # Parse name into last/first
                last_name, first_name = self._parse_name(full_name)
                
                member = ParliamentMember(
                    member_id=member_id,
                    full_name=full_name,
                    last_name=last_name,
                    first_name=first_name,
                    legislature=legislature
                )
                
                members.append(member)
                self.logger.debug(f"Parsed member: {full_name}")
        
        return members
    
    def _extract_member_id(self, href: str) -> Optional[str]:
        """
        Extract member ID from URL.
        
        Example: "/kvvcr/showpage.cfm?key=123" -> "123"
        """
        match = re.search(r'key=(\d+)', href)
        return match.group(1) if match else None
    
    def _parse_name(self, full_name: str) -> tuple:
        """
        Parse full name into (last_name, first_name).
        
        Common formats:
        - "De Croo Alexander" -> ("De Croo", "Alexander")
        - "Van den Heuvel Koen" -> ("Van den Heuvel", "Koen")
        - "Almaci Meyrem" -> ("Almaci", "Meyrem")
        
        Strategy: Last word is first name, rest is last name
        (Belgian convention in official documents)
        """
        parts = full_name.strip().split()
        
        if len(parts) == 0:
            return "", ""
        elif len(parts) == 1:
            return parts[0], ""
        else:
            # Last word is first name
            first_name = parts[-1]
            last_name = ' '.join(parts[:-1])
            return last_name, first_name


def load_members_from_file(
    html_file_path: str,
    legislature: int = 56
) -> List[ParliamentMember]:
    """
    Utility function to load members from pre-downloaded HTML file.
    
    Useful when website has bot protection and manual download is needed.
    
    Args:
        html_file_path: Path to saved HTML file
        legislature: Legislature number
    
    Returns:
        List of ParliamentMember objects
    
    Example:
        # Download HTML manually from browser, save to file
        members = load_members_from_file("members_56.html", legislature=56)
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    scraper = ChamberMemberScraper()
    return scraper.scrape_members(
        legislature=legislature,
        html_content=html_content
    )
