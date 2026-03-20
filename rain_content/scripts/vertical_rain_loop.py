import subprocess
import json
from pathlib import Path

def get_video_info(video_path):
    """Retrieves duration and frame rate precisely."""
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=duration,r_frame_rate",
        "-of", "json", str(video_path)
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    fps_eval = data['streams'][0]['r_frame_rate'].split('/')
    fps = float(fps_eval[0]) / float(fps_eval[1])
    duration = float(data['streams'][0]['duration'])
    return duration, fps

def extract_quick_vertical():
    # 1. Paths Configuration
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\output")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Vertical Resolution Map (9:16)
    res_map = {
        "720p":  "720:1280",
        "1080p": "1080:1920",
        "2k":    "1440:2560",
        "4k":    "2160:3840"
    }
    
    print("--- Quick 20s Vertical Extractor ---")
    
    # Resolution Selection
    print(f"Available Resolutions: {', '.join(res_map.keys())}")
    res_choice = input("Enter resolution (default 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1080:1920")
    target_w, target_h = target_res.split(':')

    # Crop Area Selection
    print("\nSelect Crop Focus Area:")
    print("[L] Left | [C] Center | [R] Right")
    crop_choice = input("Choice: ").lower().strip()
    
    crop_map = {
        "l": "0",                         # Far left
        "c": "(in_w-out_w)/2",            # Mathematical center
        "r": "in_w-out_w"                 # Far right
    }
    x_offset = crop_map.get(crop_choice, "(in_w-out_w)/2")

    video_files = list(source_dir.glob("*.mp4"))
    if not video_files: 
        print("No source videos found.")
        return
    video_input = video_files[0]
    
    # Static 20 second duration as requested
    target_seconds = 20
    final_output = output_dir / f"Quick_20s_{crop_choice.upper()}_{res_choice}.mp4"

    try:
        _, fps = get_video_info(video_input)

        print(f"\n🚀 Extracting 20 seconds with {crop_choice.upper()} crop...")
        
        # EFFICIENCY UPDATES:
        # -ss 0: Fast seek to start
        # -t 20: Stop exactly at 20 seconds
        # -c:a copy: Pass-through original audio (zero quality loss, zero CPU usage)
        # -preset ultrafast: Maximizes processing speed
        
        filter_complex = f"scale=-1:{target_h},crop={target_w}:{target_h}:{x_offset}:0,setsar=1"

        subprocess.run([
            "ffmpeg", "-y",
            "-ss", "0",                  # Seek to start
            "-i", str(video_input),      # Input file
            "-t", str(target_seconds),   # Limit duration to 20s
            "-vf", filter_complex,       # Apply crop/scale
            "-c:v", "libx264", 
            "-crf", "18", 
            "-preset", "ultrafast",      # Most efficient/fastest encoding
            "-c:a", "copy",              # PRESERVE AUDIO (Copy stream)
            str(final_output)
        ], check=True)

        print(f"\n✅ DONE! 20s Video Saved: {final_output}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    extract_quick_vertical()