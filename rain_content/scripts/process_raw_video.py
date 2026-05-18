import subprocess
import json
import math
import os
from pathlib import Path
import sys
import re

# Adds the project root to the python path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

# Explicitly import the functions FROM the specific module files
from scripts.process_video_length import process_video_length
from scripts.enhance_rain_atmosphere import enhance_rain_atmosphere
from scripts.overlay_rain_streaks import overlay_rain

# Define pipeline directory targets for automatic cleanups
INPUT_DIR_STAGE_1 = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\raw"
INPUT_DIR_STAGE_2 = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\first_processed"
INPUT_DIR_STAGE_3 = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\second_processed"

SUPPORTED_EXTS = ('.mp4', '.avi', '.mov', '.mkv', '.jpg', '.jpeg', '.png', '.bmp', '.webp')

def should_execute(function_name):
    """Prompts the user to run or skip a specific pipeline step."""
    choice = input(f"Proceed with '{function_name}'? (y to run / any other key to skip): ").strip().lower()
    return choice == 'y'

def purge_processed_inputs(target_folder, stage_name):
    """Deletes all processed media assets within a specified directory."""
    if not os.path.exists(target_folder):
        print(f"[Cleanup] Target directory does not exist: {target_folder}")
        return

    print(f"\n[Cleanup] Purging consumed input files from {stage_name} path...")
    purged_count = 0
    
    for filename in os.listdir(target_folder):
        if filename.lower().endswith(SUPPORTED_EXTS):
            file_path = os.path.join(target_folder, filename)
            try:
                os.remove(file_path)
                print(f"  - Deleted: {filename}")
                purged_count += 1
            except Exception as e:
                print(f"  - Error deleting {filename}: {e}")
                
    print(f"[Cleanup] Finished. Successfully removed {purged_count} files from {os.path.basename(target_folder)}.")

if __name__ == "__main__":
    # 1. Process Video Length
    if should_execute("Process Video Length"):
        process_video_length()
        purge_processed_inputs(INPUT_DIR_STAGE_1, "Stage 1 (Length Processing)")
        
    # 2. Enhance Rain Atmosphere
    if should_execute("Enhance Rain Atmosphere"):
        enhance_rain_atmosphere()
        purge_processed_inputs(INPUT_DIR_STAGE_2, "Stage 2 (Atmosphere Enhancement)")
        
    # 3. Overlay Rain
    if should_execute("Overlay Rain"):
        overlay_rain()
        purge_processed_inputs(INPUT_DIR_STAGE_3, "Stage 3 (Rain Streak Overlay)")