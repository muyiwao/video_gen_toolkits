#!/usr/bin/env python3

import subprocess
from pathlib import Path

def extract_2k_minute_frames():
    # 1. Define Paths
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\recorded\raw")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\recorded")
    
    # Ensure destination exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 2. Find all MP4 files
    video_files = list(source_dir.glob("*.mp4"))

    if not video_files:
        print(f"No .mp4 files found in {source_dir}")
        return

    print(f"Found {len(video_files)} videos. Extracting in 2K (1440p)...")

    for video in video_files:
        output_pattern = dest_dir / f"{video.stem}_2K_minute_%d.png"
        
        print(f"Processing: {video.name}...")

        # FFmpeg Command Improvements:
        # scale=2560:1440: Resizes to 2K resolution
        # force_original_aspect_ratio=increase: Ensures the image fills the 1440p frame
        # crop=2560:1440: Centers and crops to ensure exactly 16:9
        # setsar=1: Sets Sample Aspect Ratio to 1:1 to prevent stretching
        # -q:v 2: High quality output for the PNG files
        command = [
            "ffmpeg",
            "-y",
            "-i", str(video),
            "-vf", "fps=1/60,scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,setsar=1",
            "-q:v", "2",
            str(output_pattern)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            print(f"Successfully saved 2K frames for {video.name}")
        else:
            print(f"Error processing {video.name}: {result.stderr.decode('utf-8')}")

    print("\nAll 2K extractions complete.")

if __name__ == "__main__":
    extract_2k_minute_frames()