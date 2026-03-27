#!/usr/bin/env python3

import subprocess
import os
from pathlib import Path

def upscale_videos():
    # 1. Configuration & Runtime Input
    resolutions = {
        "1": ("1080p", 1920),
        "2": ("2k", 2560),
        "3": ("4k", 3840),
        "4": ("8k", 7680)
    }

    print("--- Video Upscale Tool ---")
    print("Select target resolution:")
    for key, (label, width) in resolutions.items():
        print(f"{key}. {label} ({width}px)")
    
    choice = input("\nEnter number (1-4) or press Enter for 2K: ").strip()
    
    # Logic to select resolution based on input
    selected = resolutions.get(choice, resolutions["2"])
    target_res_label = selected[0]
    target_width = selected[1]

    # 2. Path Setup
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output") / f"upscaled_{target_res_label}"
    
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 3. Find all MP4 files
    video_files = list(source_dir.glob("*.mp4"))

    if not video_files:
        print(f"❌ No .mp4 files found in {source_dir}")
        return

    print(f"\n🚀 Found {len(video_files)} videos. Upscaling to {target_res_label.upper()}...")

    for video in video_files:
        output_file = dest_dir / f"{video.stem}_{target_res_label.upper()}.mp4"
        
        print(f"\n🎬 Processing: {video.name} -> {output_file.name}")

        # Smart Scaling: Checks if Landscape or Portrait and sets the long edge to target_width
        scale_filter = (
            f"scale='if(gt(iw,ih),{target_width},-2)':'if(gt(iw,ih),-2,{target_width})':flags=lanczos"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i", str(video),
            "-vf", scale_filter,
            "-c:v", "libx264",
            "-crf", "18",         # Visually lossless
            "-preset", "slow",    # Better compression quality
            "-pix_fmt", "yuv420p", # Universal compatibility
            "-c:a", "copy",       # Stream copy audio (fast)
            str(output_file)
        ]

        # Run FFmpeg and show progress in console
        result = subprocess.run(command)

        if result.returncode == 0:
            print(f"✅ Successfully upscaled {video.name}")
        else:
            print(f"❌ Error processing {video.name}")

    print(f"\n✨ All {target_res_label.upper()} upscaling tasks complete.")

if __name__ == "__main__":
    upscale_videos()