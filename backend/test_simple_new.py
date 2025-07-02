#!/usr/bin/env python3
"""
Tests simples pour le projet.
"""

import unittest
from models import Minute


class TestMinute(unittest.TestCase):
    """Tests du modèle Minute."""
    
    def test_minute_creation(self):
        """Test de création d'une minute."""
        minute = Minute(
            ref="DOC 55 0001/001",
            date="2025-06-26",
            session="Session ordinaire 2024-2025",
            url="http://example.com",
            is_temporary=False,
            text_integral="Texte intégral test"
        )
        
        self.assertEqual(minute.ref, "DOC 55 0001/001")
        self.assertEqual(minute.date, "2025-06-26")
        self.assertEqual(minute.session, "Session ordinaire 2024-2025")
        self.assertEqual(minute.url, "http://example.com")
        self.assertFalse(minute.is_temporary)
        self.assertEqual(minute.text_integral, "Texte intégral test")
    
    def test_minute_to_dict(self):
        """Test de sérialisation."""
        minute = Minute(
            ref="DOC 55 0001/001",
            date="2025-06-26",
            session="Session ordinaire 2024-2025",
            url="http://example.com",
            is_temporary=True,
            text_integral="Texte intégral test"
        )
        
        expected = {
            'ref': "DOC 55 0001/001",
            'date': "2025-06-26",
            'session': "Session ordinaire 2024-2025",
            'url': "http://example.com",
            'is_temporary': True,
            'text_integral': "Texte intégral test"
        }
        
        self.assertEqual(minute.to_dict(), expected)


if __name__ == '__main__':
    unittest.main()
