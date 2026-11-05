from urllib.parse import urljoin
import time
from pathlib import Path
from base_web_scrapper import BaseAIPScraper

URL = "https://www.sia.aviation-civile.gouv.fr/media/dvd/eAIP_29_OCT_2026/FRANCE/AIRAC-2026-10-29/html/eAIP/"

class SiaFranceScraper(BaseAIPScraper):
    def get_icao_prefixes(self) -> tuple:
        return ("LF", "SO", "TF", "FM", "NW", "NT")

    def process_airport(self, page, icao: str, charts_dir: Path):
        # Build the aerodrome page URL using urljoin
        aerodrome_url = urljoin(URL, f"FR-AD-2.{icao}-fr-FR.html")
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
                    row = locator.locator("xpath=ancestor::tr")
                    link_text = row.inner_text().strip()
            except Exception:
                link_text = ""

            prefix_to_remove = f"AD_2_{icao}_"
            if link_text.startswith(prefix_to_remove):
                link_text = link_text[len(prefix_to_remove):]

            link_text = link_text.replace("_", " ")

            charts.append((full_url, link_text))

        return charts