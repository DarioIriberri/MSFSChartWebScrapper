from scrapper_spain import SpainScraper
from scrapper_france import FranceScraper
from scrapper_italy import ItalyScraper
from scrapper_germany import GermanyScraper
from scrapper_portugal import PortugalScraper
from scrapper_netherlands import NetherlandsScraper
from scrapper_austria import AustriaScraper

BASE_DIR = r"Z:\MSFS2020\Airports"

def download_spain():
    print("\n--- Processing Spain ---")
    SpainScraper(BASE_DIR).execute(headless=True)

def download_france():
    print("\n--- Processing France ---")
    FranceScraper(BASE_DIR).execute(headless=True)

def download_italy():
    print("\n--- Processing Italy ---")
    ItalyScraper(BASE_DIR).execute(headless=True)

def download_germany():
    print("\n--- Processing Germany ---")
    GermanyScraper(BASE_DIR).execute(headless=True)

def download_portugal():
    print("\n--- Processing Portugal ---")
    PortugalScraper(BASE_DIR).execute(headless=True)

def download_netherlands():
    print("\n--- Processing Netherlands ---")
    NetherlandsScraper(BASE_DIR).execute(headless=False)

def download_austria():
    print("\n--- Processing Austria ---")
    AustriaScraper(BASE_DIR).execute(headless=True)

if __name__ == "__main__":
    print("=== STARTING AIP CHARTS DOWNLOAD ===")

    # Comment or uncomment based on what you want to execute
    # download_spain()
    # download_france()
    # download_italy()
    # download_germany()
    # download_portugal()
    # download_netherlands()
    download_austria()

    print("\n=== ALL PROCESSES COMPLETED! ===")