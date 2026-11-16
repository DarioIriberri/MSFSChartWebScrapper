import os
import shutil
import subprocess
import msvcrt


def main():
  appdata_dir = os.environ.get('APPDATA', '')
  base_dir = os.path.join(appdata_dir, 'Microsoft Flight Simulator')
  config_dir = os.path.join(base_dir, 'ConfigsBackup-RTX-2080-Ti')
  exe_dir = r'C:\Games\Microsoft Flight Simulator'

  print('Select flight profile:')
  print('[1] Ultra  (Render Res. 150 / LODs 200 / Texture Res. Ultra)')
  print('[2] High   (Render Res. 100 / LODs 200 / Texture Res. Ultra)')
  print('[3] Medium (Render Res. 100 / LODs 150 / Texture Res. Ultra)')
  print('[4] Lite   (Render Res. 100 / LODs 150 / Texture Res. High)')
  print('\nChoose an option (1, 2, 3): ', end='', flush=True)

  # Captures keypress, no need to press enter afterwards
  key_press = msvcrt.getch().decode('utf-8', errors='ignore')
  print(key_press)  # Displays the key pressed on screen

  profile_map = {
      '1': 'UserCfg_Ultra.opt',
      '2': 'UserCfg_High.opt',
      '3': 'UserCfg_Medium.opt',
      '4': 'UserCfg_Lite.opt',
  }

  if key_press not in profile_map:
    print('Invalid choice. Aborting.')
    return

  source_file = os.path.join(config_dir, profile_map[key_press])
  dest_file = os.path.join(base_dir, 'UserCfg.opt')

  try:
    print('Applying profile...')
    shutil.copy2(source_file, dest_file)
  except Exception as e:
    print(f'Error copying configuration file: {e}')
    os.system('pause')
    return

  print(f'Launching MSFS 2020 with config file {profile_map[key_press]}')
  try:
    subprocess.Popen(
        [os.path.join(exe_dir, 'FlightSimulator.exe')], cwd=exe_dir
    )
  except Exception as e:
    print(f'Error launching simulator: {e}')
    os.system('pause')


if __name__ == '__main__':
  main()
  
# pyinstaller --onefile --icon="msfs2020.ico" --name "MSFS2020 Launcher" MSFS2020_Launcher.py