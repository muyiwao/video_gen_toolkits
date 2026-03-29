import subprocess
import json
import math
import os
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

def select_audio_file(audio_dir):
    """Lists mp3 files and lets the user choose one."""
    audio_files = list(audio_dir.glob("*.mp3"))
    if not audio_files:
        print(f"❌ No MP3 files found in {audio_dir}")
        return None
    
    print("\n🎵 Available Audio Tracks:")
    for i, file in enumerate(audio_files, 1):
        print(f"{i}. {file.name}")
    
    while True:
        try:
            choice = int(input("\nSelect audio number: "))
            if 1 <= choice <= len(audio_files):
                return audio_files[choice - 1]
            print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a number.")

def create_ultra_long_loop():
    # 1. Paths Configuration
    data_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_live")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Path where your MP3s are stored
    audio_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\sounds")

    # 2. Vertical Resolution Map (9:16)
    res_map = {
        "480p":  "480:854",
        "720p":  "720:1280",
        "1080p": "1080:1920",
        "2k":    "1440:2560",
        "4k":    "2160:3840"
    }
    
    print(f"--- Vertical Seamless Looper (Long Form) ---")
    
    # NEW: Audio Selection Phase
    audio_path = select_audio_file(audio_base_dir)
    if not audio_path:
        return

    print(f"\nAvailable Resolutions: {', '.join(res_map.keys())}")
    res_choice = input("Enter resolution (e.g., 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1080:1920")

    try:
        target_minutes = int(input("Enter length in MINUTES (3Mins Yield 1Min): "))
        target_seconds = target_minutes * 60
    except ValueError: 
        print("Invalid minute input.")
        return

    video_files = list(data_dir.glob("*.mp4"))
    if not video_files: 
        print("No source videos found in output_live.")
        return
    # Always picks the first mp4 in output_live as the loop source
    video_input = video_files[0]

    tile_file = data_dir / "temp_master_tile.mp4"
    segment_file = data_dir / "temp_1min_segment.mp4"
    temp_no_audio = data_dir / "temp_silent_final.mp4"
    list_file = data_dir / "concat_list.txt"
    final_output = data_dir / f"Vertical_Final_{res_choice}_{target_minutes}min.mp4"

    try:
        duration, fps = get_video_info(video_input)
        fade_dur = 1.0 
        loop_duration = duration - fade_dur

        print(f"\n[1/4] Creating Vertical Seamless Tile from {video_input.name}...")
        filter_complex_tile = (
            f"[0:v]scale={target_res}:force_original_aspect_ratio=increase,crop={target_res},setsar=1,split[main][over];"
            f"[over]trim=start=0:end={fade_dur},setpts=PTS-STARTPTS[fadein];"
            f"[main]trim=start={fade_dur},setpts=PTS-STARTPTS[base];"
            f"[fadein]format=pix_fmts=yuva420p,fade=t=in:st=0:d={fade_dur}:alpha=1[alpha_fade];"
            f"[base][alpha_fade]overlay=x=0:y=0:shortest=1[v]"
        )

        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_input),
            "-filter_complex", filter_complex_tile,
            "-map", "[v]", "-r", str(fps),
            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
            str(tile_file)
        ], check=True)

        print("[2/4] Building 1-minute segment...")
        tiles_needed = math.ceil(60 / loop_duration)
        with open(list_file, "w") as f:
            for _ in range(tiles_needed):
                # Using tile_file.name for the concat list
                f.write(f"file '{tile_file.name}'\n")
        
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", "-t", "60", str(segment_file)
        ], check=True)

        print(f"[3/4] Assembling {target_minutes}min Silent Video...")
        with open(list_file, "w") as f:
            for _ in range(target_minutes):
                f.write(f"file '{segment_file.name}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-map", "0:v", "-t", str(target_seconds),
            "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", 
            str(temp_no_audio)
        ], check=True)

        print(f"[4/4] Finalizing with Audio: {audio_path.name}...")
        subprocess.run([
            "ffmpeg", "-y", 
            "-i", str(temp_no_audio), 
            "-stream_loop", "-1", 
            "-i", str(audio_path),
            "-map", "0:v", 
            "-map", "1:a", 
            "-c:v", "copy", 
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(final_output)
        ], check=True)

        print(f"\n✅ SUCCESS! Vertical Loop Saved: {final_output.name}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Final cleanup of temp files
        for temp in [tile_file, segment_file, list_file, temp_no_audio]:
            if temp.exists():
                try: temp.unlink()
                except: pass

if __name__ == "__main__":
    create_ultra_long_loop()