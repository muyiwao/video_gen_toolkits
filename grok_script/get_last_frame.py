#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path

def get_latest_mp4(folder_path: Path) -> Path:
    """
    Returns the most recently modified MP4 file in the given folder.
    """
    mp4_files = list(folder_path.glob("*.mp4"))

    if not mp4_files:
        raise FileNotFoundError(f"No .mp4 files found in: {folder_path}")

    # Sort by modification time (newest first)
    mp4_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    return mp4_files[0]

def extract_last_frame(mp4_path: Path) -> Path:
    """
    Uses ffmpeg to extract the absolute final frame from the MP4 file.
    """
    output_path = mp4_path.with_name(f"{mp4_path.stem}_frame.png")

    # Command explanation:
    # -sseof -1: Fast-forward to 1 second before the end
    # -vf "select='eq(n,0)'": Grabs the last available frame in this context
    # -update 1: Ensures a single image file is written
    command = [
        "ffmpeg",
        "-y",
        "-sseof", "-1", 
        "-i", str(mp4_path),
        "-vf", "select='eq(n,0)'",
        "-vframes", "1",
        "-update", "1",
        str(output_path)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed:\n{result.stderr.decode('utf-8')}"
        )

    return output_path

def main():
    # SET YOUR PATH HERE
    folder = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\movie\series_1\episode_1")

    if not folder.exists() or not folder.is_dir():
        print(f"Error: The path {folder} is not a valid directory.")
        return

    try:
        latest_mp4 = get_latest_mp4(folder)
        print(f"Latest MP4 found: {latest_mp4.name}")

        output_frame = extract_last_frame(latest_mp4)
        print(f"Final frame extracted successfully: {output_frame.name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()