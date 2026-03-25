import subprocess
import re
from pathlib import Path

def validate_timestamp(ts):
    """Checks if the timestamp matches HH:MM:SS or MM:SS format."""
    return bool(re.match(r'^(\d{1,2}:)?([0-5]?\d):([0-5]?\d)$', ts))

def extract_video_by_timestamp():
    # 1. Path Configuration
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # List available MP4s
    videos = list(source_dir.glob("*.mp4"))
    if not videos:
        print(f"❌ No MP4 videos found in: {source_dir}")
        return

    print("\n" + "="*60)
    print("🎥 RAIN CONTENT SELECTOR: TIMESTAMP EXTRACTION")
    print("="*60)
    
    for i, v in enumerate(videos):
        print(f" [{i}] --> {v.name}")
    
    print("="*60)

    try:
        # Index Selection Guidance
        print(f"\n👉 ENTER INDEX: Type a number (0 to {len(videos)-1}) and press Enter.")
        user_input = input("Selection: ").strip()
        
        if not user_input.isdigit() or int(user_input) >= len(videos):
            print("❌ Invalid selection. Please restart and choose a valid index.")
            return

        selected_video = videos[int(user_input)]
        
        # 2. Timestamp Entry with Formatting Guidance
        print(f"\n✅ Processing: {selected_video.name}")
        print("-" * 30)
        print("REQUIRED FORMAT: HH:MM:SS (Hours:Minutes:Seconds)")
        print("Example: 00:02:15 for 2 mins and 15 seconds.")
        print("-" * 30)
        
        start_time = input("Enter START timestamp: ").strip()
        if not validate_timestamp(start_time):
            print("❌ Start time format error. Use HH:MM:SS.")
            return

        end_time = input("Enter END timestamp:   ").strip()
        if not validate_timestamp(end_time):
            print("❌ End time format error. Use HH:MM:SS.")
            return
        
        # 3. Define Output
        output_name = f"CUT_{selected_video.stem}.mp4"
        output_path = dest_dir / output_name

        # 4. FFmpeg Command
        # -ss before -i: Extremely fast seeking for large files
        # -to: Absolute timestamp for the end point
        # -c copy: Zero quality loss (Stream Copy)
        command = [
            "ffmpeg", "-y",
            "-ss", start_time,
            "-i", str(selected_video),
            "-to", end_time,
            "-c", "copy",
            "-map", "0", 
            str(output_path)
        ]

        print(f"\n🎬 Cutting video segment... (No re-encoding, preserving quality)")
        subprocess.run(command, check=True)
        
        print("\n" + "*"*30)
        print(f"✨ SUCCESS!")
        print(f"📁 Saved to: {dest_dir.name}\\{output_name}")
        print("*"*30)

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    extract_video_by_timestamp()