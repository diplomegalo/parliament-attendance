import unittest
from backend.database import (
    insert_minute,
    insert_minutes_bulk,
    minute_exists_list,
)


class DummyMinute:
    def __init__(self):
        self.ref = "TST1"
        self.date = "2025-08-20"
        self.session = "Test Session"
        self.url = "http://example.com"
        self.is_temporary = False
        self.text_integral = "Ceci est un texte de test."
        self.id = None


class TestDatabase(unittest.TestCase):
    def test_insert_minute(self):
        minute = DummyMinute()
        insert_minute(minute)
        self.assertIsNotNone(minute.id)

    def test_insert_minute_bulk(self):
        minutes = [DummyMinute() for _ in range(5)]
        for i, minute in enumerate(minutes):
            minute.ref = f"TST{i+1}"
            minute.url = f"http://example.com/{i+1}"
        insert_minutes_bulk(minutes)
        self.assertTrue(minute_exists_list([minute.ref for minute in minutes]))


if __name__ == "__main__":
    unittest.main()
