from urllib.parse import urljoin
import time
from pathlib import Path
from base_web_scrapper import BaseAIPScraper

URL = "https://eaip.lvnl.nl/AIRAC%20AMDT%2011-2026_2026_10_29/eAIP/"

class NetherlandsScraper(BaseAIPScraper):
    def get_icao_prefixes(self) -> tuple:
        return ("EH",)

    def setup_session(self, page):
        pass

    def process_airport(self, page, icao: str):
        # Build the aerodrome page URL using urljoin
        aerodrome_url = urljoin(URL, f"EH-AD 2 {icao} 1-en-GB.html")
        page.goto(aerodrome_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        pdf_locators = page.locator("a[href*='.pdf']").all()
        charts = []

        for locator in pdf_locators:
            href = locator.get_attribute("href")
            if not href:
                continue

            # urljoin cleanly resolves absolute, relative, and leading-slash URLs
            full_url = urljoin(URL, href)

            try:
                link_text = locator.inner_text().strip()
                if not link_text:
                    container = locator.locator(
                        "xpath=ancestor::td[1] | ancestor::tr[1]"
                    )
                    spans = container.locator("span").all()
                    parts = [
                        " ".join(s.inner_text().split())
                        for s in spans
                        if s.inner_text().strip()
                    ]
                    link_text = " ".join(parts).strip()
            except Exception:
                link_text = ""

            prefix_to_remove = f"AD_2_{icao}_"
            if link_text.startswith(prefix_to_remove):
                link_text = link_text[len(prefix_to_remove):]

            link_text = link_text.replace("_", " ")
            charts.append((full_url, link_text))

        return charts