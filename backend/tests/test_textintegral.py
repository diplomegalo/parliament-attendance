import unittest
from backend.entities.minute import TextIntegral


class TestTextIntegral(unittest.TestCase):
    def setUp(self):
        with open(
            "./backend/tests/mock/text-integral.html", "r", encoding="utf-8"
        ) as f:
            self.text_html = f.read()

    def test_fetch_minister(self):
        textintegral = TextIntegral("plop", self.text_html)
        result = textintegral.fetch_minister()
        self.assertIsNotNone(result)
