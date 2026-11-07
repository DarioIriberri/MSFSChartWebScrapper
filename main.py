from scrapper_spain import EnaireSpainScraper
from scrapper_france import SiaFranceScraper
from scrapper_italy import EnavItalyScraper

BASE_DIR = r"Z:\MSFS2020\Airports"

def download_spain():
    print("\n--- Processing Spain (ENAIRE) ---")
    EnaireSpainScraper(BASE_DIR).execute(headless=True)

def download_france():
    print("\n--- Processing France (SIA) ---")
    SiaFranceScraper(BASE_DIR).execute(headless=True)

def download_italy():
    print("\n--- Processing Italy (ENAV) ---")
    EnavItalyScraper(BASE_DIR).execute(headless=True)

if __name__ == "__main__":
    print("=== STARTING AIP CHARTS DOWNLOAD ===")

    # Comment or uncomment based on what you want to execute
    # download_spain()
    # download_france()
    download_italy()

    print("\n=== ALL PROCESSES COMPLETED! ===")