from abc import ABC, abstractmethod
import os
import time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright


class BaseAIPScraper(ABC):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.allowed_types = ("ADC", "APDC", "GMC", "IAC", "SID", "STAR")

    @abstractmethod
    def get_icao_prefixes(self) -> str:
        pass

    @abstractmethod
    def setup_session(self, page):
        pass

    @abstractmethod
    def process_airport(self, page, icao: str):
        pass

    def clean_name(self, text: str) -> str:
        clean_str = "".join(c for c in text if c.isalnum() or c in (" ", "_", "-", ".")).strip()
        return " ".join(clean_str.split())

    def download_file(self, full_url: str, file_path: Path, page=None) -> bool:
        """Downloads a file using the active Playwright page context to handle

        secure cookies and avoid SSL handshake errors, with a fallback to requests.
        """
        try:
            if page:
                # Use Playwright's APIRequestContext to fetch binaries securely within the session
                response = page.request.get(full_url)
                if response.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.body())
                    return True
            else:
                # Fallback mechanism if page context is omitted
                response = requests.get(full_url, timeout=15, verify=True)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    return True
        except Exception as e:
            print(f"  Error downloading {full_url}: {e}")
        return False

    def execute(self, headless=True, pause=1):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()

            self.setup_session(page)

            prefix = self.get_icao_prefixes()

            for folder_name in os.listdir(self.base_dir):
                folder_path = self.base_dir / folder_name

                if folder_path.is_dir() and len(folder_name) >= 4:
                    icao = folder_name[:4].upper()

                    if not icao.startswith(prefix):
                        continue

                    print(f"Processing airport: {icao} ({folder_name})")

                    charts_dir = folder_path / "Charts"
                    # --- CHECK IF CHARTS FOLDER EXISTS AND IS NOT EMPTY ---
                    if charts_dir.exists() and any(charts_dir.glob("*.pdf")):
                        print(f"Skipping {icao} ({folder_name}): 'Charts' folder already exists and contains files.")
                        continue
                    # ------------------------------------------
                    charts_dir.mkdir(exist_ok=True)

                    try:
                        charts = self.process_airport(page, icao)

                        downloaded_count = 0
                        seen_urls = set()

                        for full_url, desc_text in charts:
                            if not full_url or full_url in seen_urls:
                                continue
                            seen_urls.add(full_url)

                            if desc_text:
                                clean_filename = self.clean_name(desc_text)
                                filename = f"{icao} {clean_filename}.pdf"
                            else:
                                filename = full_url.split("/")[-1].split("?")[0]
                                filename = self.clean_name(filename)
                                if not filename.endswith(".pdf"):
                                    filename = f"{icao}_chart_{downloaded_count + 1}.pdf"

                            # --- GLOBAL FILTER ---
                            # Verify if file name contains one of the allowed types
                            if not any(chart_type in filename.upper() for chart_type in self.allowed_types):
                                continue
                            # ---------------------

                            file_path = charts_dir / filename

                            if self.download_file(full_url, file_path, page):
                                downloaded_count += 1
                                time.sleep(pause)

                        print(f"-> Success! {downloaded_count} charts saved in {charts_dir}\n")

                    except Exception as e:
                        print(f"Error processing {icao}: {e}\n")

            browser.close()
            print("Download process completed!")