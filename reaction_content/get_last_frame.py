#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

def get_dancing_mp4(folder_path: Path) -> Path:
    """
    Returns the most recently modified MP4 file that contains 'dancing' in the name.
    """
    # Filter for files containing 'dancing' (case-insensitive)
    mp4_files = [
        f for f in folder_path.glob("*.mp4") 
        if "dancing" in f.name.lower()
    ]

    if not mp4_files:
        raise FileNotFoundError(f"No .mp4 files with 'dancing' in the name found in: {folder_path}")

    # Sort by modification time (newest first) to get the latest version
    mp4_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    return mp4_files[0]

def extract_last_frame(mp4_path: Path) -> Path:
    """
    Uses ffmpeg to extract the absolute final frame from the MP4 file.
    """
    # Output path remains in the same directory as requested
    output_path = mp4_path.with_name(f"{mp4_path.stem}_last_frame.png")

    # Command explanation:
    # -sseof -0.1: Starts seeking 0.1 seconds before the end
    # -update 1: Overwrites to a single image
    command = [
        "ffmpeg",
        "-y",
        "-sseof", "-0.1", 
        "-i", str(mp4_path),
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
    # Paths are identical for source and destination as requested
    working_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\video_pools")

    if not working_dir.exists() or not working_dir.is_dir():
        print(f"Error: The path {working_dir} is not a valid directory.")
        return

    try:
        # 1. Find the target video
        target_video = get_dancing_mp4(working_dir)
        print(f"🎯 Target 'Dancing' Video: {target_video.name}")

        # 2. Extract the frame
        output_frame = extract_last_frame(target_video)
        print(f"✨ Last frame saved as: {output_frame.name}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()