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

def create_ultra_long_loop():
    # 1. Paths Configuration
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. User Inputs
    res_map = {
        "480p":  "854:480",
        "720p":  "1280:720",
        "1080p": "1920:1080",
        "2k":    "2560:1440",
        "4k":    "3840:2160"
    }
    
    print(f"Available Resolutions: {', '.join(res_map.keys())}")
    res_choice = input("Enter resolution (e.g., 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1920:1080")

    try:
        target_minutes = int(input("Enter length in MINUTES: "))
        target_seconds = target_minutes * 60
    except ValueError: return

    video_files = list(source_dir.glob("*.mp4"))
    if not video_files: return
    video_input = video_files[0]

    tile_file = output_dir / "temp_master_tile.mp4"
    segment_file = output_dir / "temp_1min_segment.mp4"
    list_file = output_dir / "concat_list.txt"
    final_output = output_dir / f"Final_{res_choice}_{target_minutes}min.mp4"

    try:
        duration, fps = get_video_info(video_input)
        
        # We define a crossfade duration (1 second or 0.5 for very short clips)
        fade_dur = 1.0 if duration > 3 else 0.5
        # The usable length of the loop after the overlap
        loop_duration = duration - fade_dur

        print(f"\n[1/3] Creating Seamless Tile (Fade: {fade_dur}s)...")
        
        # This filter takes the video, splits it, and overlays the start onto the end
        # with a linear alpha fade-in to create a perfect loop.
        filter_complex = (
            f"[0:v]scale={target_res}:force_original_aspect_ratio=increase,crop={target_res},setsar=1,split[main][over];"
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

        # STAGE 2: Create a 1-Minute Segment using the Tile
        print("[2/3] Building intermediate segment...")
        tiles_needed = math.ceil(60 / loop_duration)
        with open(list_file, "w") as f:
            for _ in range(tiles_needed):
                f.write(f"file '{tile_file.name}'\n")
        
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", "-t", "60", str(segment_file)
        ], check=True)

        # STAGE 3: Final Assembly
        print(f"[3/3] Final Assembly to {target_minutes} minutes...")
        with open(list_file, "w") as f:
            for _ in range(target_minutes):
                f.write(f"file '{segment_file.name}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", "-t", str(target_seconds), str(final_output)
        ], check=True)

        print(f"\nDONE! Path: {final_output}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        for temp in [tile_file, segment_file, list_file]:
            if temp.exists(): temp.unlink()

if __name__ == "__main__":
    create_ultra_long_loop()