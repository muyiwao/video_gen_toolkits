#!/usr/bin/env python3

import subprocess
from pathlib import Path

def extract_frames():
    # --- 1. Define Paths ---
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\images")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # --- 2. File Selection ---
    video_files = list(source_dir.glob("*.mp4"))
    if not video_files:
        print(f"No .mp4 files found in {source_dir}")
        return

    print("\n--- High-Quality Frame Extraction Tool ---")
    
    # --- 3. Resolution Selection ---
    print("\nSelect Output Resolution:")
    print("1. 1080p (1920x1080) | 2. 2K (2560x1440) | 3. 4K (3840x2160) | 4. Custom")
    res_choice = input("Selection (1-4): ").strip()
    
    res_map = {"1": "1920:1080", "2": "2560:1440", "3": "3840:2160"}
    target_res = res_map.get(res_choice, input("Enter custom res (W:H): ") if res_choice == "4" else "2560:1440")
    t_w, t_h = target_res.split(":")

    # --- 4. Extraction Mode ---
    print("\nSelect Extraction Mode:")
    print("1. Batch Mode (Every X seconds)")
    print("2. Single Frame (Specific timestamp)")
    mode = input("Select mode (1/2): ").strip()

    vf_chain = f"scale={target_res}:force_original_aspect_ratio=increase:flags=lanczos,crop={t_w}:{t_h},setsar=1"

    for video in video_files:
        print(f"\n--- Processing: {video.name} ---")
        
        # --- NEW: Range Selection Logic ---
        print("Set Time Range (Press ENTER for entire video)")
        start_t = input("  Start Time (HH:MM:SS or seconds): ").strip()
        end_t = input("  End Time (HH:MM:SS or seconds): ").strip()

        # Build time range arguments
        time_args = []
        if start_t: time_args += ["-ss", start_t]
        if end_t:   time_args += ["-to", end_t]

        if mode == '1':
            # --- BATCH MODE ---
            try:
                interval = float(input(f"  Enter interval in SECONDS (e.g., 60): "))
            except ValueError:
                print("  Invalid input, skipping batch...")
                continue
            
            output_pattern = dest_dir / f"{video.stem}_{t_h}p_batch_%03d.png"
            
            # Note: We put time_args BEFORE -i for faster seeking on the start point
            command = [
                "ffmpeg", "-y"
            ] + time_args + [
                "-i", str(video),
                "-vf", f"fps=1/{interval},{vf_chain}",
                "-q:v", "2", str(output_pattern)
            ]

        else:
            # --- SINGLE FRAME MODE ---
            timestamp = input(f"  Enter specific timestamp (HH:MM:SS): ").strip()
            safe_ts = timestamp.replace(':', '-')
            output_file = dest_dir / f"{video.stem}_{t_h}p_frame_{safe_ts}.png"
            
            command = [
                "ffmpeg", "-y", 
                "-ss", timestamp, 
                "-i", str(video),
                "-vf", vf_chain,
                "-frames:v", "1", 
                "-q:v", "2", str(output_file)
            ]

        # --- 5. Execution ---
        print(f"  🚀 Exporting to {target_res}...")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"  ✅ Successfully saved {t_h}p frames for {video.name}")
        else:
            print(f"  ❌ Error: {result.stderr}")

    print("\n✨ All extraction tasks complete.")

if __name__ == "__main__":
    extract_frames()