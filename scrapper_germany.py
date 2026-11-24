import base64
import io
import re
from pathlib import Path
from urllib.parse import unquote, urljoin

from PIL import Image, ImageFilter
from base_web_scrapper import BaseAIPScraper

AERO_IFR_URL = "https://aip.aero/de/en/ifr/"


class DfsGermanyScraper(BaseAIPScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Match both ICAO/generic short codes and DFS long chart titles
        self.allowed_types = (
            "ADC",
            "GROUND",
            "GROUND MOVEMENT CHART",
            "PARKING",
            "PARKINGDOCKING CHART",
            "PARKING/DOCKING CHART",
            "AERODROME CHART",
            "DEPARTURE ROUTES SID",
            "ARRIVAL ROUTES STAR",
            "ILS",
            # "RNP",
            "IAC",
            "DEPARTURE CHART",
            "APPROACH CHART",
            "ARRIVAL CHART",
            "VISUAL",
            "LVP",
        )
        self.excluded_tokens = (
            "TABULAR DESCRIPTION",
            "FAS DATA BLOCK",
            "FAS-DATA BLOCK",
            "ROUTES",
            # "STANDARD INSTRUMENT ARRIVAL ROUTES",
            # "STANDARD INSTRUMENT DEPARTURE ROUTES",
            # # "ARRIVAL ROUTES",
            # # "DEPARTURE ROUTES",
        )

    def get_icao_prefixes(self) -> tuple:
        return ("ED",)

    def setup_session(self, page):
        pass

    def _find_dfs_chapter_url(self, page, icao: str) -> str | None:
        icao = icao.upper()
        target_url = f"{AERO_IFR_URL}?{icao}"
        page.goto(target_url, wait_until="networkidle", timeout=30000)

        links = page.locator("a[href]").all()
        for loc in links:
            href = loc.get_attribute("href") or ""
            if "aip.dfs.de/BasicIFR/" in href and ("/chapter/" in href or "/pages/" in href):
                return urljoin(page.url, href)
        return None

    def _is_allowed_chart(self, title: str, url: str) -> bool:
        haystack = f"{title} {url}".upper()

        # Drop tabular descriptions, FAS data blocks, and non-chart route sheets
        if any(bad in haystack for bad in self.excluded_tokens):
            return False

        if not self.allowed_types:
            return True

        return any(token.upper() in haystack for token in self.allowed_types)

    def process_airport(self, page, icao: str):
        icao = icao.upper()
        chapter_url = self._find_dfs_chapter_url(page, icao)
        if not chapter_url:
            print(f"[-] No DFS chapter link found for {icao}")
            return []

        page.goto(chapter_url, wait_until="networkidle", timeout=30000)

        charts = []
        seen_urls = set()

        for loc in page.locator("a[href]").all():
            href = loc.get_attribute("href")
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            full_url = urljoin(page.url, href)
            if full_url in seen_urls:
                continue

            # Filter relevant chart links (direct PDFs, DFS wrapper pages, or chart resources)
            if not re.search(r"(\.pdf|/pages/|/documents/|chart)", full_url, re.I):
                continue

            seen_urls.add(full_url)

            try:
                title = " ".join(loc.inner_text().split())
            except Exception:
                title = ""

            if not title or len(title) > 100:
                slug = full_url.split("/")[-1].split("?")[0]
                title = unquote(slug)

            if not self._is_allowed_chart(title, full_url):
                continue

            charts.append((full_url, title))

        return charts

    def download_file(self, full_url: str, file_path: Path, page=None) -> bool:
        """Extracts embedded base64 chart images from DFS HTML pages and saves as PDF."""
        is_dfs_html_page = "aip.dfs.de" in full_url and full_url.lower().endswith(".html")

        if not is_dfs_html_page:
            return super().download_file(full_url, file_path, page=page)

        if page is None:
            print(f"  Playwright page is required to render DFS HTML chart: {full_url}")
            return False

        try:
            page.goto(full_url, wait_until="networkidle", timeout=30000)

            img_locator = page.locator("img#imgAIP, img.pageimage").first
            src = img_locator.get_attribute("src") or ""

            if not src.startswith("data:image/") or "," not in src:
                print(f"  No embedded base64 image found in DFS page: {full_url}")
                return False

            base64_payload = src.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_payload)
            pdf_path = file_path.with_suffix(".pdf")
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            with Image.open(io.BytesIO(image_bytes)) as img:
                rgb_img = img.convert("RGB")

                # Optional 2x upscale with smooth interpolation before saving as PDF
                w, h = rgb_img.size
                rgb_img = rgb_img.resize((w * 2, h * 2), Image.Resampling.BICUBIC)

                # Optional micro-blur (keep radius small, e.g. 0.4 - 0.7, or omit if too soft)
                # rgb_img = rgb_img.filter(ImageFilter.GaussianBlur(radius=0.5))

                rgb_img.save(pdf_path, "PDF", resolution=300.0)

            return True

        except Exception as e:
            print(f"  Error converting DFS HTML chart {full_url} to PDF: {e}")
            return False