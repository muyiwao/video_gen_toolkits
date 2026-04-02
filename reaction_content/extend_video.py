import subprocess
import math
import os
from pathlib import Path

def get_video_info(file_path):
    """Uses ffprobe to get duration and resolution reliably."""
    cmd = [
        "ffprobe", "-v", "error", 
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "csv=p=0", 
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    
    # Standardize the output format
    parts = result.replace('\n', ',').split(',')
    parts = [p.strip() for p in parts if p.strip()]
    
    try:
        width = int(parts[0])
        height = int(parts[1])
        duration = float(parts[2])
        return width, height, duration
    except (IndexError, ValueError) as e:
        print(f"❌ Error parsing video metadata. Result was: {result}")
        raise e

def fast_extend_video():
    # --- 1. Path Configuration ---
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_long")
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_list = output_dir / "concat_list.txt"

    # --- 2. Selection ---
    files = sorted(list(source_dir.glob("*.mp4")) + list(source_dir.glob("*.mov")))
    if not files: 
        print("No files found in input directory.")
        return
        
    for i, f in enumerate(files, 1):
        print(f"{i}. {f.name}")
    
    try:
        choice_input = input(f"\nSelect video (1-{len(files)}): ").strip()
        if not choice_input: return
        
        choice = int(choice_input)
        selected_video = files[choice - 1]
        
        target_minutes = float(input("Enter desired length in MINUTES: "))
        target_seconds = target_minutes * 60
    except (ValueError, IndexError):
        print("❌ Invalid input.")
        return

    # --- 3. Metadata Extraction ---
    w, h, duration = get_video_info(selected_video)
    loops_needed = math.ceil(target_seconds / duration)
    
    orientation = "Vertical" if h > w else "Horizontal"
    print(f"\n🎥 Detected {orientation} Video: {w}x{h}")
    print(f"⚡ Generating {loops_needed} loops for {target_minutes} min total...")
    
    # Write the concat list
    with open(temp_list, "w", encoding="utf-8") as f:
        for _ in range(loops_needed):
            path_str = str(selected_video.absolute()).replace("\\", "/")
            f.write(f"file '{path_str}'\n")

    output_file = output_dir / f"LOOPED_{target_minutes}m_{selected_video.name}"

    # --- 4. Fixed Fast Command ---
    # -fflags +genpts: Regenerates timestamps to prevent Non-monotonic DTS errors
    # -map_metadata -1: Removes cover art/metadata causing "Unknown cover type"
    # -avoid_negative_ts make_zero: Further stabilizes the concat points
    command = [
        "ffmpeg", "-y",
        "-fflags", "+genpts", 
        "-f", "concat",
        "-safe", "0",
        "-i", str(temp_list),
        "-t", str(target_seconds),
        "-map_metadata", "-1",
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        str(output_file)
    ]

    try:
        print(f"🚀 Processing...")
        subprocess.run(command, check=True, capture_output=True)
        print(f"\n✅ SUCCESS! Looped {orientation} video saved.")
        print(f"📍 Location: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ FFmpeg failed!")
        print(e.stderr.decode())
    finally:
        if temp_list.exists():
            temp_list.unlink()

if __name__ == "__main__":
    fast_extend_video()