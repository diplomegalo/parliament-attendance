import unittest

from bs4 import BeautifulSoup
from sync_job import fetch_minutes_from_page


class DummyWebPage:
    def __init__(self):
        with open(
            "./backend/tests/mock/parliament_page_20250819_144523.html",
            "r",
            encoding="utf-8"
        ) as f:
            content = f.read()
            self.str_content = content
            self.soup_content = BeautifulSoup(content, "html.parser")

    def get_str(self):
        return self.str_content

    def get_soup(self):
        return self.soup_content


class TestSyncJob(unittest.TestCase):
    def test_insert_minutes(self):
        page = DummyWebPage()
        minutes = fetch_minutes_from_page(page.get_soup())
        self.assertGreater(len(minutes), 0, "Aucune minute récupérée")
        for minute in minutes:
            self.assertIsNotNone(minute.ref, "Référence manquante")
