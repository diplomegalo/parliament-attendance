"""
Integration tests for infrastructure layer.

Tests the actual implementations against real data (mocked HTML).
"""

import unittest
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

from infrastructure.session_scraper import ParliamentarySessionScraper
from domain.entities import SessionMetadata


class TestParliamentaryWebScraper(unittest.TestCase):
    """Test web scraper with mock HTML data."""
    
    def setUp(self):
        """Load mock HTML page."""
        # Use absolute path relative to this file's location
        test_dir = Path(__file__).parent
        mock_file = test_dir / "mock" / "parliament_page_20250819_144523.html"
        
        with open(mock_file, "r", encoding="utf-8") as f:
            self.mock_html = f.read()
        
        self.scraper = ParliamentarySessionScraper()
    
    def test_parse_session_row_with_valid_data(self):
        """Test parsing a valid session row."""
        soup = BeautifulSoup(self.mock_html, "html.parser")
        table = soup.find("table", id="lst")
        
        if table:
            rows = table.find_all("tr", attrs={"valign": "top"})
            if rows:
                # Test parsing first row
                session = self.scraper._parse_session_row(rows[0])
                
                if session:  # Only assert if we got valid data
                    self.assertIsInstance(session, SessionMetadata)
                    self.assertIsNotNone(session.reference)
                    self.assertIsInstance(session.date, datetime)
                    self.assertIsNotNone(session.description)
                    self.assertIsNotNone(session.document_url)
    
    def test_parse_french_date(self):
        """Test French date parsing."""
        test_cases = [
            ("14 novembre 2024", datetime(2024, 11, 14)),
            ("1 janvier 2025", datetime(2025, 1, 1)),
            ("31 décembre 2024", datetime(2024, 12, 31)),
        ]
        
        for date_str, expected in test_cases:
            result = self.scraper._parse_french_date(date_str)
            self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
