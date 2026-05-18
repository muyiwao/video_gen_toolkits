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

def should_execute(function_name):
    """Prompts the user to run or skip a specific pipeline step."""
    choice = input(f"Proceed with '{function_name}'? (y to run / any other key to skip): ").strip().lower()
    return choice == 'y'

if __name__ == "__main__":
    # 1. Process Video Length
    if should_execute("Process Video Length"):
        process_video_length()
        
    # 2. Enhance Rain Atmosphere
    if should_execute("Enhance Rain Atmosphere"):
        enhance_rain_atmosphere()
        
    # 3. Overlay Rain
    if should_execute("Overlay Rain"):
        overlay_rain()
        