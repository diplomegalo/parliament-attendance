"""
Unit tests for member scraper infrastructure.
"""

import unittest
from pathlib import Path
from infrastructure.scrapers.member_scraper import (
    ChamberMemberScraper,
    ParliamentMember,
    load_members_from_file
)


class TestParliamentMember(unittest.TestCase):
    """Test ParliamentMember domain entity."""
    
    def test_member_creation(self):
        """Test creating a member with all fields."""
        member = ParliamentMember(
            member_id="123",
            full_name="De Croo Alexander",
            last_name="De Croo",
            first_name="Alexander",
            party="OpenVLD",
            constituency="Oost-Vlaanderen",
            legislature=56
        )
        
        self.assertEqual(member.member_id, "123")
        self.assertEqual(member.full_name, "De Croo Alexander")
        self.assertEqual(member.last_name, "De Croo")
        self.assertEqual(member.first_name, "Alexander")
        self.assertEqual(member.party, "OpenVLD")
        self.assertEqual(member.legislature, 56)
    
    def test_name_normalization(self):
        """Test that extra whitespace is normalized."""
        member = ParliamentMember(
            member_id="456",
            full_name="Van  den   Heuvel    Koen",
            last_name="Van  den   Heuvel",
            first_name="  Koen  ",
            party="N-VA",
            constituency="Antwerpen",
            legislature=56
        )
        
        # Should normalize to single spaces
        self.assertEqual(member.full_name, "Van den Heuvel Koen")
        self.assertEqual(member.last_name, "Van den Heuvel")
        self.assertEqual(member.first_name, "Koen")
    
    def test_invalid_legislature_raises_error(self):
        """Test that invalid legislature raises ValueError."""
        with self.assertRaises(ValueError) as context:
            ParliamentMember(
                member_id="789",
                full_name="Test Member",
                last_name="Test",
                first_name="Member",
                party="Party",
                constituency="District",
                legislature=0
            )
        
        self.assertIn("Legislature must be a positive integer", str(context.exception))
        
        with self.assertRaises(ValueError):
            ParliamentMember(
                member_id="790",
                full_name="Test Member",
                last_name="Test",
                first_name="Member",
                party="Party",
                constituency="District",
                legislature=-5
            )


class TestChamberMemberScraper(unittest.TestCase):
    """Test member scraper functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = ChamberMemberScraper()
    
    def test_extract_member_id(self):
        """Test extracting member ID from various URL formats."""
        test_cases = [
            ("/kvvcr/showpage.cfm?key=123", "123"),
            ("showpage.cfm?section=test&key=456&lang=fr", "456"),
            ("/depute/cvlist54.cfm?key=789", "789"),
            ("no_key_here.cfm", None),
            ("", None)
        ]
        
        for href, expected_id in test_cases:
            result = self.scraper._extract_member_id(href)
            self.assertEqual(
                result,
                expected_id,
                f"Failed for href: {href}"
            )
    
    def test_parse_name_simple(self):
        """Test parsing simple single-word names."""
        test_cases = [
            ("Almaci Meyrem", ("Almaci", "Meyrem")),
            ("Bertels Jan", ("Bertels", "Jan")),
            ("Bouchez Georges-Louis", ("Bouchez", "Georges-Louis"))
        ]
        
        for full_name, (expected_last, expected_first) in test_cases:
            last, first = self.scraper._parse_name(full_name)
            self.assertEqual(last, expected_last)
            self.assertEqual(first, expected_first)
    
    def test_parse_name_compound(self):
        """Test parsing compound last names."""
        test_cases = [
            ("De Croo Alexander", ("De Croo", "Alexander")),
            ("Van den Heuvel Koen", ("Van den Heuvel", "Koen")),
            ("Van der Straeten Tinne", ("Van der Straeten", "Tinne")),
            ("De Smet François", ("De Smet", "François"))
        ]
        
        for full_name, (expected_last, expected_first) in test_cases:
            last, first = self.scraper._parse_name(full_name)
            self.assertEqual(
                last,
                expected_last,
                f"Last name mismatch for: {full_name}"
            )
            self.assertEqual(
                first,
                expected_first,
                f"First name mismatch for: {full_name}"
            )
    
    def test_parse_name_edge_cases(self):
        """Test edge cases in name parsing."""
        # Single word (no first name)
        last, first = self.scraper._parse_name("SingleName")
        self.assertEqual(last, "SingleName")
        self.assertEqual(first, "")
        
        # Empty string
        last, first = self.scraper._parse_name("")
        self.assertEqual(last, "")
        self.assertEqual(first, "")
        
        # Extra whitespace
        last, first = self.scraper._parse_name("  Doe   John  ")
        self.assertEqual(last, "Doe")
        self.assertEqual(first, "John")
    
    def test_parse_member_table_with_sample_html(self):
        """Test parsing with sample HTML structure."""
        sample_html = """
        <html>
        <body>
            <table>
                <tr>
                    <td>
                        <a href="/kvvcr/showpage.cfm?key=123">
                            De Croo Alexander
                        </a>
                    </td>
                    <td>OpenVLD</td>
                    <td>Oost-Vlaanderen</td>
                </tr>
                <tr>
                    <td>
                        <a href="/kvvcr/showpage.cfm?key=456">
                            Almaci Meyrem
                        </a>
                    </td>
                    <td>Groen</td>
                    <td>Brussel</td>
                </tr>
                <tr>
                    <td>Not a link</td>
                    <td>Invalid</td>
                    <td>Row</td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        members = self.scraper.scrape_members(
            legislature=56,
            html_content=sample_html
        )
        
        # Should parse 2 valid members, skip invalid row
        self.assertEqual(len(members), 2)
        
        # Check first member
        self.assertEqual(members[0].member_id, "123")
        self.assertEqual(members[0].full_name, "De Croo Alexander")
        self.assertEqual(members[0].last_name, "De Croo")
        self.assertEqual(members[0].first_name, "Alexander")
        self.assertEqual(members[0].party, "OpenVLD")
        self.assertEqual(members[0].constituency, "Oost-Vlaanderen")
        self.assertEqual(members[0].legislature, 56)
        
        # Check second member
        self.assertEqual(members[1].member_id, "456")
        self.assertEqual(members[1].full_name, "Almaci Meyrem")
        self.assertEqual(members[1].party, "Groen")
    
    def test_parse_empty_table(self):
        """Test parsing with no valid member data."""
        sample_html = """
        <html>
        <body>
            <table>
                <tr>
                    <td>Header 1</td>
                    <td>Header 2</td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        members = self.scraper.scrape_members(
            legislature=56,
            html_content=sample_html
        )
        
        # Should return empty list, not crash
        self.assertEqual(len(members), 0)
    
    def test_parse_no_tables(self):
        """Test parsing HTML with no tables."""
        sample_html = "<html><body><p>No tables here</p></body></html>"
        
        with self.assertRaises(ValueError) as context:
            self.scraper.scrape_members(
                legislature=56,
                html_content=sample_html
            )
        
        self.assertIn("No tables found", str(context.exception))


class TestLoadMembersFromFile(unittest.TestCase):
    """Test utility function for loading from file."""
    
    def test_load_from_nonexistent_file(self):
        """Test loading from file that doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            load_members_from_file("/nonexistent/file.html")
    
    def test_load_from_file_integration(self):
        """Test loading from actual file if test data exists."""
        # Check if test HTML file exists
        test_file = Path(__file__).parent / "mock" / "members_56.html"
        
        if test_file.exists():
            members = load_members_from_file(str(test_file), legislature=56)
            self.assertGreater(len(members), 0)
            self.assertTrue(all(m.legislature == 56 for m in members))


if __name__ == '__main__':
    unittest.main()
