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

if __name__ == "__main__":
    process_video_length()
    enhance_rain_atmosphere()
    overlay_rain()