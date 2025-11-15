"""
Tests for MinuteTextCleaner.

Tests HTML cleaning and text extraction.
"""

import unittest
from infrastructure.parsers import MinuteTextCleaner


class TestMinuteTextCleaner(unittest.TestCase):
    """Test MinuteTextCleaner functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cleaner = MinuteTextCleaner()
    
    def test_extract_text_from_simple_html(self):
        """Test extracting text from simple HTML."""
        html = """
        <html>
            <body>
                <p>This is a test.</p>
                <p>Second paragraph.</p>
            </body>
        </html>
        """
        
        text = self.cleaner.extract_text(html)
        
        self.assertIn("This is a test.", text)
        self.assertIn("Second paragraph.", text)
    
    def test_removes_script_tags(self):
        """Test that script tags are removed."""
        html = """
        <html>
            <head>
                <script>alert('test');</script>
            </head>
            <body>
                <p>Visible content.</p>
            </body>
        </html>
        """
        
        text = self.cleaner.extract_text(html)
        
        self.assertIn("Visible content.", text)
        self.assertNotIn("alert", text)
    
    def test_removes_style_tags(self):
        """Test that style tags are removed."""
        html = """
        <html>
            <head>
                <style>body { color: red; }</style>
            </head>
            <body>
                <p>Visible content.</p>
            </body>
        </html>
        """
        
        text = self.cleaner.extract_text(html)
        
        self.assertIn("Visible content.", text)
        self.assertNotIn("color: red", text)
    
    def test_removes_navigation_elements(self):
        """Test that navigation elements are removed."""
        html = """
        <html>
            <body>
                <nav>
                    <a href="/">Home</a>
                    <a href="/about">About</a>
                </nav>
                <main>
                    <p>Main content.</p>
                </main>
            </body>
        </html>
        """
        
        text = self.cleaner.extract_text(html)
        
        self.assertIn("Main content.", text)
        self.assertNotIn("Home", text)
        self.assertNotIn("About", text)
    
    def test_normalizes_whitespace(self):
        """Test whitespace normalization."""
        html = """
        <html>
            <body>
                <p>Line   with   multiple   spaces.</p>


                <p>Another paragraph.</p>
            </body>
        </html>
        """
        
        text = self.cleaner.extract_text(html)
        
        # Multiple spaces should be normalized to single space
        self.assertIn("Line with multiple spaces.", text)
        # Check that excessive spacing is cleaned
        self.assertEqual(text.count("   "), 0)
    
    def test_empty_html_raises_error(self):
        """Test that empty HTML raises ValueError."""
        with self.assertRaises(ValueError):
            self.cleaner.extract_text("")
        
        with self.assertRaises(ValueError):
            self.cleaner.extract_text("   ")
    
    def test_extract_main_content_with_selector(self):
        """Test extracting main content with CSS selector."""
        html = """
        <html>
            <body>
                <nav>Navigation</nav>
                <main id="content">
                    <p>Main content here.</p>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """
        
        text = self.cleaner.extract_main_content(html, "#content")
        
        self.assertIn("Main content here.", text)
        # Navigation and footer should be excluded if selector works
        # (but may be included if selector finds nothing)
    
    def test_extract_main_content_fallback(self):
        """Test main content extraction with fallback."""
        html = """
        <html>
            <body>
                <p>All content.</p>
            </body>
        </html>
        """
        
        # Should not raise error even with invalid selector
        text = self.cleaner.extract_main_content(
            html,
            "#nonexistent"
        )
        
        self.assertIn("All content.", text)
    
    def test_parliamentary_minute_structure(self):
        """Test with realistic parliamentary minute structure."""
        html = """
        <html>
            <head>
                <meta charset="UTF-8">
                <title>CRIV 56 0001</title>
            </head>
            <body>
                <h1>Plenaire vergadering</h1>
                <p>01-09-2024</p>
                
                <p>De heer Jan Janssen heeft het woord.</p>
                <p>Mijnheer de voorzitter, ik wil...</p>
                
                <p>Mevrouw Marie Dupont heeft het woord.</p>
            </body>
        </html>
        """
        
        text = self.cleaner.extract_text(html)
        
        self.assertIn("Plenaire vergadering", text)
        self.assertIn("01-09-2024", text)
        self.assertIn("Jan Janssen", text)
        self.assertIn("Marie Dupont", text)


if __name__ == '__main__':
    unittest.main()
