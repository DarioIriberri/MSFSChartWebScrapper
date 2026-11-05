from urllib.parse import urljoin
import time
from pathlib import Path
from base_web_scrapper import BaseAIPScraper

URL = "https://aip.enaire.es/AIP/"


class EnaireScraper(BaseAIPScraper):
    def get_icao_prefixes(self) -> tuple:
        return ("LE", "GC")

    def process_airport(self, page, icao: str, charts_dir: Path):
        page.goto(URL, wait_until="networkidle", timeout=30000)
        time.sleep(4)

        pdf_locators = page.locator("a[href*='.pdf']").all()
        charts = []

        for locator in pdf_locators:
            href = locator.get_attribute("href")
            if not href or icao not in href:
                continue

            # urljoin cleanly resolves whether it is relative, absolute, or starts with /
            full_url = urljoin(URL, href)

            try:
                row = locator.locator("xpath=ancestor::tr")
                desc_text = row.locator("td.desc").inner_text().strip()
            except Exception:
                desc_text = ""

            charts.append((full_url, desc_text))

        return charts