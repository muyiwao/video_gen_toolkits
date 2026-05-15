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

from scripts.pre_processing import process_video_length, enhance_rain_atmosphere, overlay_rain_streaks


if __name__ == "__main__":
 process_video_length()
 enhance_rain_atmosphere()
 overlay_rain_streaks()