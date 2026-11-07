import time
from urllib.parse import urljoin, unquote
from urllib.parse import urljoin
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
from base_web_scrapper import BaseAIPScraper
from bs4 import BeautifulSoup

EAIP_MENU_URL = "https://onlineservices.enav.it/enavWebPortalStatic/AIP/AIP/(A11-26)_2026_10_29/eAIP/menu.html"
USERNAME = "derp@gmail.com"
PASSWORD = "derp"


class EnavItalyScraper(BaseAIPScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.menu_html = ""
        # Broaden allowed types with keywords found in ENAV chart titles
        self.allowed_types = (
            "SID",
            "STAR",
            "APPROACH",
            "AERODROME CHART",
            "PARKING",
            "GROUND",
            "VISUAL",
            # "OBSTACLE",
            "LOW VISIBILITY"
        )

    def get_icao_prefixes(self) -> tuple:
        return ("LI",)

    def setup_session(self, page) -> str:
        """Launches a visible Chromium instance, handles Oracle Cloud login if required,

        waits for manual 2FA entry, and retrieves the e-AIP menu HTML content.
        """
        print(f"[INFO] Navigating to e-AIP Portal: {EAIP_MENU_URL}")
        page.goto(EAIP_MENU_URL)

        # Detect if redirected to Oracle Identity Cloud Service login
        if (
            "identity.oraclecloud.com" in page.url
            or "signin" in page.url
            or "oracle" in page.url.lower()
        ):
            print(
                "[INFO] Oracle Identity Cloud login detected. Submitting credentials..."
            )

            # Wait for username input field and fill credentials
            username_selector = (
                'input[type="text"], input[name="username"], #username'
            )
            page.wait_for_selector(username_selector, timeout=15000)
            page.fill(username_selector, USERNAME)

            # Check if password field is immediately available or requires clicking 'Next'
            password_selector = 'input[type="password"], #password'
            if not page.locator(password_selector).is_visible():
                # Click next if Oracle multi-step login is active
                next_button = page.locator('#idcs-signin-basic-signin-form-submit button, button[type="submit"]').first
                if next_button.is_visible():
                    next_button.click()

            page.wait_for_selector(password_selector, timeout=15000)
            page.fill(password_selector, PASSWORD)

            # Submit initial login form targeting the inner button directly
            submit_btn = page.locator('#idcs-signin-basic-signin-form-submit button').first
            if submit_btn.is_visible():
                submit_btn.click()

            print(
                "\n" + "=" * 60
            )
            print(
                "Please enter your 2FA/MFA code in the browser window if necessary."
            )
            print(
                "=" * 60 + "\n"
            )

            # Wait for authentication completion (redirect back to ENAV static portal domain)
            try:
                page.wait_for_url(
                    lambda url: "enavWebPortalStatic" in url
                    or "eAIP" in url,
                    timeout=120000,  # 2 minutes window for 2FA completion
                )
                print(
                    "[SUCCESS] Authentication successful! Accessing e-AIP menu..."
                )
            except PlaywrightTimeoutError:
                print(
                    "[ERROR] Timed out waiting for 2FA authentication."
                )
                return ""

        # Ensure we are on the target menu frame URL
        if page.url != EAIP_MENU_URL:
            page.goto(EAIP_MENU_URL)

        page.wait_for_load_state("networkidle")

        # Extract full HTML source of the e-AIP menu
        html_content = page.content()
        print(
            f"[SUCCESS] Retreived menu HTML ({len(html_content)} characters)."
        )

        # Keep session open briefly to allow inspection/further navigation
        time.sleep(3)

        # with open("C:/enav.html", "w", encoding="utf-8") as f:
        #     f.write(html_content)
        self.menu_html = html_content
        return html_content

    def process_airport(self, page, icao: str):
        """Locates the given airport's ICAO code in the cached menu HTML,

        navigates directly to its e-AIP document page, and extracts all PDF links
        as tuples of (url, title/description).
        """
        import re

        icao = icao.upper()
        soup = BeautifulSoup(self.menu_html, "html.parser")

        # Search for the anchor tag whose href contains 'LI-AD' and the specified ICAO code
        pattern = re.compile(rf"LI-AD.*?\b{icao}\b", re.IGNORECASE)
        target_a = None

        for a_tag in soup.find_all("a", href=True):
            if pattern.search(a_tag["href"]):
                target_a = a_tag
                break

        if not target_a:
            print(f"[-] Airport link not found in the menu for ICAO: {icao}")
            return []

        # Build the absolute URL using the menu base URL
        relative_href = target_a["href"]
        airport_url = urljoin(EAIP_MENU_URL, relative_href)
        print(f"[+] Navigating directly to airport page for {icao}: {airport_url}")

        # Navigate directly to the airport's specific HTML page via Playwright with a timeout
        try:
            page.goto(airport_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            print(f"[-] Error or timeout loading page for {icao}: {e}")
            return []

        # Extract all chart/document PDF links and descriptions from the airport page
        charts = []
        anchors = page.query_selector_all('a[href$=".pdf"], a[href*=".pdf"]')

        for a in anchors:
            pdf_href = a.get_attribute("href")
            full_url = urljoin(page.url, pdf_href)

            # Clean up raw inner text: replace newlines/tabs with spaces and collapse multiple spaces
            raw_title = a.inner_text()
            title = " ".join(raw_title.split())

            # Fallback if text is empty or too messy, use filename from URL and unquote it
            if not title or len(title) > 80:
                filename_from_url = full_url.split("/")[-1].split("?")[0].replace(".pdf", "")
                # Decode URL encoding (e.g. %20 -> space, %2F -> /)
                title = unquote(filename_from_url)

            # Append as a tuple (full_url, description) to match BaseAIPScraper expectations
            charts.append((full_url, title))

        return charts