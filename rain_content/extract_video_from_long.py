import subprocess
import os
from pathlib import Path

def extract_video_to_destination():
    # 1. Path Configuration
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw")
    # Define your specific destination folder here
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    
    # Create destination if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # List available MP4s in source
    videos = list(source_dir.glob("*.mp4"))
    if not videos:
        print(f"❌ No MP4 videos found in: {source_dir}")
        return

    print("\n--- Available Videos ---")
    for i, v in enumerate(videos):
        print(f"{i}: {v.name}")
    
    try:
        choice = int(input("\nSelect video index to cut: "))
        selected_video = videos[choice]
        
        # 2. Get Timestamps
        print(f"\nEditing: {selected_video.name}")
        start_time = input("Enter START (hh:mm:ss): ").strip()
        end_time = input("Enter END (hh:mm:ss): ").strip()
        
        # 3. Define Output Path
        output_name = f"CUT_{selected_video.stem}.mp4"
        output_path = dest_dir / output_name

        # 4. FFmpeg Command
        # -ss before -i is faster for long videos
        # -c copy ensures 0% quality loss
        command = [
            "ffmpeg", "-y",
            "-ss", start_time,
            "-i", str(selected_video),
            "-to", end_time,
            "-c", "copy",
            "-map", "0", 
            str(output_path)
        ]

        print(f"\n🎬 Exporting to: {output_path}")
        subprocess.run(command, check=True)
        print(f"\n✅ Success! Clip saved to: {dest_dir}")

    except (ValueError, IndexError):
        print("❌ Invalid selection. Please choose a number from the list.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    extract_video_to_destination()