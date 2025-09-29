import logging
import re

from bs4 import BeautifulSoup
from typing import Optional
from backend.entities.minister import Minister


class Minute:
    ministers = set()

    def __init__(
        self,
        id: Optional[int] = None,
        ref: str = "",
        date: str = "",
        session: str = "",
        url: str = "",
        is_temporary: bool = False,
        text_integral: str = ""
    ):
        """
        Initialize a Minute object.

        Args:
            id: Database ID (optional, auto-generated)
            ref: Reference identifier for the minute
            date: Date of the parliamentary session
            session: Session description/name
            url: URL to the full document
            is_temporary: Whether this is a temporary/provisional version
            text_integral: Full text content of the minute
        """
        self.id = id
        self.ref = ref
        self.date = date
        self.session = session
        self.url = url
        self.is_temporary = is_temporary
        self.text_integral = text_integral

    def fetch_minister(self):
        soup = BeautifulSoup(self.text_integral, 'html.parser')

        # Find the specific section in the HTML
        # Set position to : "DETAIL DES VOTES NOMINATIFS"
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

        elements = detail_section.parent.find_all_next(
            "span"
        )

        forbiden_tokens = [
            "oui", "non", "abstention", "ja", "nee", "Onthoudingen"
        ]

        for element in elements:
            inner_text = element.get_text(separator=" ", strip=True).lower()
            if any(token in inner_text for token in forbiden_tokens):
                continue
            elif inner_text.strip() == "":
                continue
            elif inner_text.replace(" ", "").isdigit():
                continue
            elif ":" in inner_text:
                continue
            else:
                self.ministers.add(Minister(name=inner_text))

            return self.ministers
