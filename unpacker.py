import time
from pathlib import Path
import shutil
import rarfile

# --- PATH CONFIGURATION ---
# Root directory where your airports are saved with their .rar files
SOURCE_DIR = Path(r"Z:\MSFS2020\Airports\tmp")

# Destination directory where you want the folders ready for Addons Linker
DEST_DIR = Path(r"Z:\MSFS2020\Community_Organized")

# Optional: If UnRAR is not in your Windows PATH, uncomment and point to your executable:
rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe"

tt=time.time()

def unpack_airport_rars():
  DEST_DIR.mkdir(parents=True, exist_ok=True)

  if not SOURCE_DIR.exists():
    print(f"Error: The source path {SOURCE_DIR} does not exist.")
    return

  print(f"Scanning airports in: {SOURCE_DIR}")

  for airport_folder in SOURCE_DIR.iterdir():
    if not airport_folder.is_dir():
      continue

    # Look for .rar files inside the airport folder
    rar_files = list(airport_folder.glob("*.rar"))
    if not rar_files:
      continue

    rar_path = rar_files[0]  # Take the first .rar found in the airport folder
    print(f"\nProcessing: {airport_folder.name} -> {rar_path.name}")

    try:
      with rarfile.RarFile(rar_path) as rf:
        # Analyze internal structure to identify the mod's root folder
        namelist = rf.namelist()
        top_levels = set(Path(name).parts[0] for name in namelist if name)

        if not top_levels:
          print("  [WARNING] The RAR file appears to be empty.")
          continue

        # Temporary internal directory for clean extraction
        temp_extract_dir = DEST_DIR / "_temp_extraction"
        temp_extract_dir.mkdir(exist_ok=True)

        # Extract everything into the temp folder
        rf.extractall(temp_extract_dir)

        # Process each main folder found inside the RAR
        for top_folder in top_levels:
          extracted_path = temp_extract_dir / top_folder

          if extracted_path.is_dir():
            # Build the new name by prepending "AIRPORT "
            new_folder_name = f"AIRPORT {top_folder}"
            final_dest_path = DEST_DIR / new_folder_name

            if final_dest_path.exists():
              print(
                  f"  -> The folder '{new_folder_name}' already exists in"
                  " destination. Skipping."
              )
            else:
              # Move and rename the folder directly to the final destination
              shutil.move(str(extracted_path), str(final_dest_path))
              print(f"  -> Success: Created folder '{new_folder_name}'")
              print(f"Elapsed: {time.time()-tt}")

        # Clean up the temporary directory if any traces remain
        if temp_extract_dir.exists():
          shutil.rmtree(temp_extract_dir, ignore_errors=True)

    except rarfile.BadRarFile:
      print(
          "  [ERROR] The RAR file is corrupted or not valid:"
          f" {rar_path.name}"
      )
    except Exception as e:
      print(f"  [ERROR] Unexpected error processing {rar_path.name}: {e}")

  print("\nUnpacking and renaming process completed!")
  print(f"Elapsed: {time.time() - tt}")


if __name__ == "__main__":
  unpack_airport_rars()