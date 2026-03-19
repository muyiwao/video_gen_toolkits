import subprocess
import json
import math
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

def create_vertical_loop():
    # 1. Paths Configuration
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Vertical Resolution Map (9:16)
    res_map = {
        "720p":  "720:1280",
        "1080p": "1080:1920",
        "2k":    "1440:2560",
        "4k":    "2160:3840"
    }
    
    print("--- Vertical (9:16) Video Generator ---")
    
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

    try:
        duration_input = input("\nEnter length (e.g., '60s' or '1m'): ").lower().strip()
        if duration_input.endswith('s'):
            target_seconds = int(duration_input[:-1])
        elif duration_input.endswith('m'):
            target_seconds = int(duration_input[:-1]) * 60
        else:
            target_seconds = int(duration_input) * 60
    except ValueError: 
        print("Invalid duration format.")
        return

    video_files = list(source_dir.glob("*.mp4"))
    if not video_files: 
        print("No source videos found.")
        return
    video_input = video_files[0]

    tile_file = output_dir / "temp_master_tile.mp4"
    list_file = output_dir / "concat_list.txt"
    final_output = output_dir / f"Vertical_{crop_choice.upper()}_{target_seconds}s.mp4"

    try:
        duration, fps = get_video_info(video_input)
        fade_dur = 1.0 if duration > 3 else 0.5
        loop_duration = duration - fade_dur

        print(f"\n[1/2] Cropping to {crop_choice.upper()} and Creating Loop...")
        
        # FILTER LOGIC:
        # We scale height first, then crop using the dynamic x_offset
        filter_complex = (
            f"[0:v]scale=-1:{target_h},crop={target_w}:{target_h}:{x_offset}:0,setsar=1,split[main][over];"
            f"[over]trim=start=0:end={fade_dur},setpts=PTS-STARTPTS[fadein];"
            f"[main]trim=start={fade_dur},setpts=PTS-STARTPTS[base];"
            f"[fadein]format=pix_fmts=yuva420p,fade=t=in:st=0:d={fade_dur}:alpha=1[alpha_fade];"
            f"[base][alpha_fade]overlay=x=0:y=0:shortest=1[v]"
        )

        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_input),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-r", str(fps),
            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
            str(tile_file)
        ], check=True)

        # STAGE 2: Final Assembly
        print(f"[2/2] Stitching to {target_seconds} seconds...")
        tiles_needed = math.ceil(target_seconds / loop_duration)
        
        with open(list_file, "w") as f:
            for _ in range(tiles_needed):
                f.write(f"file '{tile_file.name}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", "-t", str(target_seconds), str(final_output)
        ], check=True)

        print(f"\nSUCCESS! Vertical video saved to: {final_output}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if tile_file.exists(): tile_file.unlink()
        if list_file.exists(): list_file.unlink()

if __name__ == "__main__":
    create_vertical_loop()