from urllib.parse import urljoin
import re
import time
from base_web_scrapper import BaseAIPScraper

URL = "file:///Z:/Downloads/1795174847862_AIS_EAIP_ISO_26NOV2026/eAIP/html/eAIP/"


class PortugalScraper(BaseAIPScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_types = (
            "AERODROME CHART",
            "PARKING",
            "GROUND MOVEMENT",
            "GROUND_MOVEMENT",
            "DEPARTURE CHART",
            "SID",
            "ARRIVAL CHART",
            "STAR",
            "INSTRUMENT APPROACH CHART",
        )

    def get_icao_prefixes(self) -> tuple:
        return ("LP",)

    def setup_session(self, page):
        pass

    def process_airport(self, page, icao: str):
        aerodrome_url = urljoin(URL, f"LP-AD-2.{icao}-en-PT.html")
        page.goto(aerodrome_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        charts = []
        # Locate PDF links inside the charts table (AD 2.24)
        pdf_links = page.locator("a[href*='.pdf']").all()

        for locator in pdf_links:
            href = locator.get_attribute("href")
            if not href:
                continue

            full_url = urljoin(aerodrome_url, href)

            # Find the link's row and its associated name cell
            row = locator.locator("xpath=ancestor::tr[1]")
            cells = row.locator("td")

            chart_name = ""
            if cells.count() >= 2:
                # Standard case: first cell = Name, last cell = Page/PDF
                chart_name = cells.first.inner_text().strip()
            else:
                # If the name is in the row above due to rowspan="2", check the previous tr
                prev_row = row.locator("xpath=preceding-sibling::tr[1]")
                if prev_row.count() > 0:
                    chart_name = prev_row.locator("td").first.inner_text().strip()

            if not chart_name:
                continue

            # Basic cleanup for filenames: normalize dashes and whitespace
            clean_name = chart_name.replace("\u2013", "-").replace("\u2014", "-")
            clean_name = re.sub(r"\s+", " ", clean_name).strip()

            charts.append((full_url, clean_name))

        return charts