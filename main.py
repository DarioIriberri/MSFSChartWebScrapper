from scrapper_spain import EnaireScraper
from scrapper_france import SiaFranceScraper

BASE_DIR = r"Z:\MSFS2020\Airports"

def download_spain():
    print("\n--- Processing Spain (ENAIRE) ---")
    enaire = EnaireScraper(BASE_DIR)
    enaire.execute(headless=True)

def download_france():
    print("\n--- Processing France (SIA) ---")
    francia = SiaFranceScraper(BASE_DIR)
    francia.execute(headless=True)

if __name__ == "__main__":
    print("=== STARTING AIP CHARTS DOWNLOAD ===")

    # Comment or uncomment based on what you want to execute
    download_spain()
    download_france()

    print("\n=== ALL PROCESSES COMPLETED! ===")