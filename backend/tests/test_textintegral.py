import unittest

from backend.text_integral import TextIntegral


class TestTextIntegral(unittest.TestCase):
    def setUp(self):
        with open(
            "./backend/tests/mock/text-integral.html", "r", encoding="utf-8"
        ) as f:
            self.text_html = f.read()

    def test_fetch_minister(self):
        textintegral = TextIntegral("plop", self.text_html)
        result = textintegral.fetch_minister()
        self.assertGreater(len(result), 0)
