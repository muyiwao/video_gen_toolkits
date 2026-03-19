#!/usr/bin/env python3

import subprocess
from pathlib import Path

def upscale_video_to_2k():
    # 1. Define Paths
    # Update these paths to match your local setup
    # source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\recorded\raw")
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\movie\series_1\episode_1\output")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\recorded\upscaled_2k")
    
    # Ensure destination exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 2. Find all MP4 files
    video_files = list(source_dir.glob("*.mp4"))

    if not video_files:
        print(f"No .mp4 files found in {source_dir}")
        return

    print(f"Found {len(video_files)} videos. Starting 2K upscaling...")

    for video in video_files:
        output_file = dest_dir / f"{video.stem}_2K.mp4"
        
        print(f"Processing: {video.name} -> {output_file.name}...")

        # FFmpeg Command for High Quality 2K Upscaling:
        # scale=2560:1440: Resizes to 2K resolution
        # :flags=lanczos: Uses a high-quality scaling algorithm for sharpness
        # -c:v libx264: Uses the standard H.264 codec
        # -crf 18: High quality setting (lower is better, 18-22 is visually lossless)
        # -preset slow: Spends more time encoding for better compression/quality
        command = [
            "ffmpeg",
            "-y",
            "-i", str(video),
            "-vf", "scale=2560:1440:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "slow",
            "-c:a", "copy",  # Copies audio without re-encoding to save time
            str(output_file)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            print(f"Successfully upscaled {video.name}")
        else:
            print(f"Error processing {video.name}: {result.stderr.decode('utf-8')}")

    print("\nAll 2K upscales complete.")

if __name__ == "__main__":
    upscale_video_to_2k()