import logging
import re

from bs4 import BeautifulSoup

from backend.models import Minister


class TextIntegral:
    ministers = set()

    def __init__(self, ref: str, text_html: str):
        self.ref = ref
        self.text_html = text_html

    def fetch_minister(self):
        # Set position to : "DETAIL DES VOTES NOMINATIFS"
        soup = BeautifulSoup(self.text_html, 'html.parser')

        # Find the specific section in the HTML
        detail_section = soup.find(
            string=re.compile(
                r"DETAIL\s+DES\s+VOTES\s+NOMINATIFS", re.IGNORECASE
            )
        )
        if detail_section is None:
            logging.error(
                (
                    "Could not find the section 'DETAIL DES VOTES NOMINATIFS' "
                    "in the HTML."
                )
            )
            return None

        logging.debug(f"Found detail section: {detail_section}")

        elements = soup.find_all_next(
            "span",
            attrs={"lang": re.compile(r"^NL", re.IGNORECASE)}
        )

        forbiden_tokens = [
            "oui", "non", "abstention", "ja", "nee", "Onthoudingen"
        ]

        for element in elements:
            inner_text = element.get_text(separator=" ", strip=True).lower()
            if any(token in inner_text for token in forbiden_tokens):
                return None
            elif inner_text.replace(" ", "").isdigit():
                return None
            elif ":" in inner_text:
                return None
            else:
                self.ministers.add(Minister(name=inner_text))

            return self.ministers
