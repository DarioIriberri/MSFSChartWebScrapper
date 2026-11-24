from urllib.parse import urljoin
import time
from pathlib import Path
from base_web_scrapper import BaseAIPScraper

URL = "https://eaip.austrocontrol.at/lo/261030/"


class AustriaScraper(BaseAIPScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_types = (
            "AERODROME CHART",
            "PARKING/DOCKING",
            "GROUND MOVEMENT",
            "SID",
            "STAR",
            "TRANSITION",
            "INSTRUMENT APPROACH",
            "VISUAL",
        )

    def get_icao_prefixes(self) -> tuple:
        return ("LO",)

    def setup_session(self, page):
        pass

    def process_airport(self, page, icao: str):
        aerodrome_url = urljoin(URL, f"ad_2_{icao.lower()}.htm")
        page.goto(aerodrome_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        pdf_locators = page.locator("a[href*='.pdf']").all()
        charts = []

        for locator in pdf_locators:
            href = locator.get_attribute("href")
            if not href:
                continue

            full_url = urljoin(page.url, href)

            try:
                row = locator.locator("xpath=ancestor::tr[1]").first
                cells = row.locator("td")

                link_text = ""
                if cells.count() >= 2:
                    desc_cell = cells.nth(1)
                    italic = desc_cell.locator("i").first
                    if italic.count() > 0:
                        link_text = " ".join(italic.inner_text().split())

                    if not link_text:
                        link_text = " ".join(desc_cell.inner_text().split())

                if not link_text:
                    link_text = " ".join(locator.inner_text().split())
            except Exception:
                link_text = ""

            link_text = link_text.replace("_", " ").strip()
            charts.append((full_url, link_text))

        return charts