from urllib.parse import urljoin
import time
from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from base_web_scrapper import BaseAIPScraper
from urllib.parse import urljoin, unquote, urlparse, parse_qs

URL_LOGIN = "https://www.ead.eurocontrol.int/cms-eadbasic/opencms/en/login/ead-basic/"
URL = "https://www.ead.eurocontrol.int/fwf-eadbasic/restricted/user/aip/aip_overview.faces"
USERNAME = "lesterice"
PASSWORD = "derpderp"

class SwitzerlandScraper(BaseAIPScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_types = (
            "AERODROME CHART",
            "PARKING",
            "GROUND MOVEMENT CHART",
            "IAC",
            "SID",
            "STAR",
            "TRANSITION",
            "VISUAL APPROACH",
            "AREA CHART",
        )

    def get_icao_prefixes(self) -> tuple:
        return ("LS",)

    def setup_session(self, page):
        print(f"[INFO] Navigating to EAD Basic login: {URL_LOGIN}")
        page.goto(URL_LOGIN, wait_until="domcontentloaded", timeout=30000)

        time.sleep(1)

        # If already authenticated or redirected away from the login form, go straight to AIP Library
        if page.locator("#usernameField").count() == 0 and page.locator('input[name="j_username"]').count() == 0:
            if "aip_overview.faces" not in page.url:
                page.goto(URL, wait_until="domcontentloaded", timeout=30000)
            return

        page.wait_for_selector("#usernameField, input[name='j_username']", timeout=15000)
        page.fill("#usernameField, input[name='j_username']", USERNAME)
        page.fill("#passwordField, input[name='j_password']", PASSWORD)

        submit_btn = page.locator("#ajaxLoginForm input[type='submit'], #ajaxLoginForm button[type='submit']").first
        submit_btn.click()

        # Wait until ajaxSubmitForm finishes without visible errors and leaves login or exposes AIP Library
        try:
            page.wait_for_function(
                """() => {
                    const err = document.querySelector('#form_errors');
                    const errVisible = err && window.getComputedStyle(err).display !== 'none' && err.textContent.trim().length > 0;
                    if (errVisible) return false;
                    return !window.location.href.includes('/login/') || document.querySelector('a[href*="aip_overview.faces"]') !== null;
                }""",
                timeout=20000,
            )
        except PlaywrightTimeoutError:
            err_text = ""
            if page.locator("#form_errors").count() > 0:
                err_text = page.locator("#form_errors").inner_text().strip()
            print(f"[WARN] Login wait timed out. Form error: {err_text or 'none'}")

        # Accept Terms and Conditions modal if it is shown
        accept_btn = page.locator("#acceptTCButton")
        try:
            accept_btn.wait_for(state="visible", timeout=5000)
            print("[INFO] Accepting EAD Basic Terms and Conditions...")
            accept_btn.click()
            page.wait_for_function(
                """() => {
                    const dlg = document.querySelector('#termsDialog');
                    return !dlg || window.getComputedStyle(dlg).display === 'none';
                }""",
                timeout=10000,
            )

            time.sleep(1)
        except PlaywrightTimeoutError:
            # Modal was not displayed in this session
            pass

    def _select_switzerland_authority(self, page):
        """Selects 'Switzerland (LS)' in the PrimeFaces SelectOneMenu if not already selected."""
        current_val = page.locator("#mainForm\\:selectAuthorityCode_input").input_value()
        if current_val == "LS":
            return

        page.locator("#mainForm\\:selectAuthorityCode .ui-selectonemenu-trigger").click()
        ls_item = page.locator(
            "#mainForm\\:selectAuthorityCode_panel tr.ui-selectonemenu-item[data-label='Switzerland (LS)']"
        ).first
        ls_item.wait_for(state="visible", timeout=10000)
        ls_item.click()
        self._wait_for_ajax_idle(page)

    def _ensure_advanced_search(self, page):
        """Enables Advanced Search so filter inputs are rendered inside advancedSearchPanel."""
        adv_input = page.locator("#mainForm\\:enableAdvancedSearch_input")
        if adv_input.count() > 0 and not adv_input.is_checked():
            page.locator("#mainForm\\:enableAdvancedSearch .ui-chkbox-box").click()
            page.wait_for_selector("#mainForm\\:documentName", state="visible", timeout=10000)

    def _wait_for_ajax_idle(self, page, timeout=15000):
        """Waits for PrimeFaces AJAX status indicator (if active) to settle."""
        try:
            page.wait_for_function(
                """() => {
                    const startEl = document.querySelector('[id$="_start"]');
                    if (!startEl) return true;
                    return window.getComputedStyle(startEl).display === 'none';
                }""",
                timeout=timeout,
            )
        except PlaywrightTimeoutError:
            pass

    def process_airport(self, page, icao: str):
        def _has_valid_pdf_link(href: str) -> bool:
            if not href:
                return False
            parsed = urlparse(href)
            qs = parse_qs(parsed.query)
            linked_target = qs.get("link", [""])[0]
            if linked_target:
                return True

            return ".pdf" in href.lower() and "link=&" not in href

        """Searches AIP Library for the given ICAO code and extracts (url, title) pairs."""
        icao = icao.upper()
        charts = []

        if (
                "aip_overview.faces" not in page.url
                or page.locator("#mainForm\\:selectAuthorityCode").count() == 0
        ):
            page.goto(URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("#mainForm\\:selectAuthorityCode", timeout=15000)

        self._select_switzerland_authority(page)
        self._ensure_advanced_search(page)

        doc_name_input = page.locator("#mainForm\\:documentName")
        doc_name_input.wait_for(state="visible", timeout=10000)
        doc_name_input.fill("")
        doc_name_input.fill(icao)

        page.locator("#mainForm\\:querySearch").click()
        self._wait_for_ajax_idle(page)

        while True:
            rows_locator = page.locator("#mainForm\\:searchResults_data tr[data-ri]")
            for row in rows_locator.all():
                cells = row.locator("td").all()
                if len(cells) < 2:
                    continue

                valid_link = None
                for cell in cells:
                    for a in cell.locator("a[href]").all():
                        href = a.get_attribute("href")
                        if _has_valid_pdf_link(href):
                            valid_link = a
                            break
                    if valid_link:
                        break

                if not valid_link:
                    continue

                href = valid_link.get_attribute("href")
                full_url = urljoin(page.url, href)

                heading = ""
                if len(cells) >= 5:
                    heading = " ".join(cells[4].inner_text().split()).strip()

                if not heading:
                    heading = " ".join(valid_link.inner_text().split()).strip()

                if not heading:
                    filename_from_url = full_url.split("/")[-1].split("?")[0].replace(".pdf", "")
                    heading = unquote(filename_from_url)

                charts.append((full_url, heading))

            next_btn = page.locator("#mainForm\\:searchResults .ui-paginator-next").first
            if next_btn.count() == 0:
                break

            btn_class = next_btn.get_attribute("class") or ""
            if "ui-state-disabled" in btn_class:
                break

            first_row_before = rows_locator.first.inner_text() if rows_locator.count() > 0 else ""
            next_btn.click()
            self._wait_for_ajax_idle(page)

            # Wait until table rows update or paginator active page changes
            try:
                page.wait_for_function(
                    """([selector, prevText]) => {
                        const firstTr = document.querySelector(selector);
                        if (!firstTr) return false;
                        return firstTr.innerText.trim() !== prevText;
                    }""",
                    arg=["#mainForm\\:searchResults_data tr[data-ri]", first_row_before.strip()],
                    timeout=10000,
                )
            except PlaywrightTimeoutError:
                break

        return charts