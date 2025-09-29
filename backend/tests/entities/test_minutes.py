import unittest
from backend.entities import Minute


class TestMinutes(unittest.TestCase):

    def test_minutes_full(self):
        minutes = Minute(
            id=1,
            ref="ref",
            date="2023-01-01",
            session="session",
            url="http://example.com",
            is_temporary=False,
            text_integral="Full text"
        )
        self.assertEqual(minutes.id, 1)
        self.assertEqual(minutes.ref, "ref")
        self.assertEqual(minutes.date, "2023-01-01")
        self.assertEqual(minutes.session, "session")
        self.assertEqual(minutes.url, "http://example.com")
        self.assertFalse(minutes.is_temporary)
        self.assertEqual(minutes.text_integral, "Full text")
