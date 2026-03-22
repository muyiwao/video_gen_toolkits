import subprocess
import json
import sys
from pathlib import Path

def get_video_info(video_path):
    """Retrieves duration and frame rate with robust error handling."""
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=duration,r_frame_rate",
        "-of", "json", str(video_path)
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            raise ValueError("FFprobe returned empty output.")
            
        data = json.loads(result.stdout)
        
        # Accessing the stream data safely
        stream = data['streams'][0]
        fps_str = stream.get('r_frame_rate', '24/1')
        num, den = map(int, fps_str.split('/'))
        fps = num / den
        
        duration = float(stream.get('duration', 20.0))
        return duration, fps
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
        print(f"⚠️ Warning: Could not probe video metadata ({e}). Using defaults: 24fps.")
        return 20.0, 24.0

def extract_quick_vertical():
    # 1. Paths Configuration    
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    img1_path = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\shorts\subscribe-cta.png")
    img2_path = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\shorts\logo-cta.png")

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
        print("❌ No video files found in source directory.")
        return
    video_input = video_files[0]
    
    target_seconds = 20
    final_output = output_dir / f"Vertical_Loop_20s_{res_choice}.mp4"

    try:
        print(f"🎬 Processing: {video_input.name}")
        _, fps = get_video_info(video_input)

        font_style = "Arial Black"
        font_size = int(target_h * 0.03) # Scale font size based on height for 4k/2k
        border_width = max(2, int(font_size * 0.05))
        
        text_x = "(w-text_w)/2"
        text_y = "h*0.1"

        img1_enable = "between(t,10,15)"
        img2_enable = "1" 

        # Using double quotes for the text to handle potential single quotes in captions
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

        cmd = [
            "ffmpeg", "-y",
            "-ss", "0", "-i", str(video_input),
            "-i", str(img1_path),
            "-i", str(img2_path),
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "0:a?", # Added '?' to make audio optional if source has none
            "-t", str(target_seconds),
            "-c:v", "libx264", "-crf", "18", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",
            str(final_output)
        ]

        subprocess.run(cmd, check=True)
        print(f"\n✅ SUCCESS! Saved to: {final_output}")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ FFmpeg Error: {e}")
    except Exception as e:
        print(f"\n❌ Script Error: {e}")

if __name__ == "__main__":
    extract_quick_vertical()