import os
from pathlib import Path
import re

# --- PATH CONFIGURATION ---
COMMUNITY_DIR = Path(r"C:\Users\dazz\AppData\Roaming\Microsoft Flight Simulator\Packages\Community")
ANDRES3D_BGL_DIR = COMMUNITY_DIR / "z-andres3d-airports-lights" / "scenery" / "andres3d"


def get_installed_icaos():
    """Scans Community folders starting with 'AIRPORT' and extracts 4-letter ICAO codes."""
    installed_icaos = set()

    if not COMMUNITY_DIR.exists():
        print(f"Error: Community folder not found at {COMMUNITY_DIR}")
        return installed_icaos

    print("Scanning installed airports in Community...")
    for item in COMMUNITY_DIR.iterdir():
        if item.is_dir() and item.name.upper().startswith("AIRPORT"):
            folder_name = item.name.lower()

            # Heurístic: Look for 4-letter blocks surrounded by hyphens, underscores, or spaces
            matches = re.findall(r'(?:^|[\-_ ])([a-z]{4})(?:[\-_ ]|$)', folder_name)

            for match in matches:
                icao = match.upper()
                # Filter out common 4-letter words that are not ICAO codes
                if icao not in {"ONLY", "LIGHT", "DTAZ"}:
                    installed_icaos.add(icao)

    print(f"-> Detected {len(installed_icaos)} unique ICAO codes in your airports.")
    return installed_icaos


def disable_conflicting_lights():
    if not ANDRES3D_BGL_DIR.exists():
        print(f"Error: Andres3D BGL path not found at {ANDRES3D_BGL_DIR}")
        return

    installed_icaos = get_installed_icaos()
    if not installed_icaos:
        print("No ICAO codes found in the airport folders.")
        return

    print(f"\nChecking .bgl files in {ANDRES3D_BGL_DIR}...")
    renamed_count = 0

    for bgl_file in ANDRES3D_BGL_DIR.glob("*.bgl"):
        bgl_name_upper = bgl_file.stem.upper()

        # Check if the BGL filename matches any of your installed airports
        if bgl_name_upper in installed_icaos:
            target_off = bgl_file.with_suffix(".off")
            if not target_off.exists():
                bgl_file.rename(target_off)
                print(f"  [DISABLED] {bgl_file.name} -> {target_off.name}")
                renamed_count += 1

    print(f"\nProcess completed! Renamed {renamed_count} .bgl files to .off to prevent lighting conflicts.")


if __name__ == "__main__":
    disable_conflicting_lights()