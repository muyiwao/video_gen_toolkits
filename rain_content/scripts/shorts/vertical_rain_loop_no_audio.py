import subprocess
import json
from pathlib import Path

def get_video_info(video_path):
    """Retrieves duration and frame rate precisely."""
    command = [
        "ffprobe", "-v", "-error", "-select_streams", "v:0",
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
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # --- ASSET PATHS ---
    img1_path = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\shorts\subscribe-cta.png")
    img2_path = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\shorts\logo-cta.png")
    # REMOVED: audio_path variable

    # 2. Vertical Resolution Map (9:16)
    res_map = {
        "720p":  "720:1280",
        "1080p": "1080:1920",
        "2k":    "1440:2560",
        "4k":    "2160:3840"
    }
    
    print("--- 20s Vertical Seamless Looper (Original Audio) ---")
    
    res_choice = input("Enter resolution (default 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1080:1920")
    target_w, target_h = map(int, target_res.split(':'))

    user_caption = input("\nEnter the caption for the video: ").strip()

    print("\nSelect Crop Focus Area: [L] Left | [C] Center | [R] Right")
    choice_input = input("Choice: ").lower().strip()
    
    crop_map = {
        "l": "0",
        "c": "(in_w-out_w)/2",
        "r": "in_w-out_w"
    }
    x_offset = crop_map.get(choice_input, "(in_w-out_w)/2")

    video_files = list(source_dir.glob("*.mp4"))
    if not video_files: 
        print("No video files found.")
        return
    video_input = video_files[0]
    
    target_seconds = 20
    final_output = output_dir / f"Vertical_Loop_20s_{res_choice}.mp4"

    try:
        _, fps = get_video_info(video_input)

        font_style = "Arial Black"
        font_size = 90 
        border_width = 4 
        
        text_x = "(w-text_w)/2"
        text_y = "h*0.1"

        img1_enable = "between(t,10,15)"
        img2_enable = "1" 

        filter_complex = (
            f"[0:v]scale=-1:{target_h},crop={target_w}:{target_h}:{x_offset}:0,setsar=1,"
            f"drawtext=text='{user_caption}':font='{font_style}':fontcolor=white:fontsize={font_size}:"
            f"x={text_x}:y={text_y}:borderw={border_width}:bordercolor=black:"
            f"fix_bounds=1[base];"
            f"[1:v]scale={target_w}:{target_h}[i1];"
            f"[2:v]scale={target_w}:{target_h}[i2];"
            f"[base][i1]overlay=0:0:enable='{img1_enable}'[temp];"
            f"[temp][i2]overlay=0:0:enable='{img2_enable}'[vout]"
        )

        # FIXED FFMPEG COMMAND
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", "0", "-i", str(video_input), # Input 0 (Video + Original Audio)
            "-i", str(img1_path),                # Input 1
            "-i", str(img2_path),                # Input 2
            "-filter_complex", filter_complex,
            "-map", "[vout]",                    # Map processed video
            "-map", "0:a",                       # Map ORIGINAL audio from Input 0
            "-t", str(target_seconds),
            "-c:v", "libx264", "-crf", "18", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",       # Keep original audio encoding clean
            str(final_output)
        ], check=True)

        print(f"\n✅ DONE! Vertical Loop Saved: {final_output}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    extract_quick_vertical()