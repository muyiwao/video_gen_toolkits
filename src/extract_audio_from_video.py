import sys
import subprocess
from pathlib import Path

# --- Module Import Setup ---
# Adds the project root to the python path to find path_picker
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

try:
    # Adjusting import to match your project structure: src/path_picker.py
    from src.path_picker import interactive_path_picker
except ImportError:
    print("❌ Could not find path_picker.py in src folder.")
    sys.exit(1)

def select_video_file(directory):
    """List videos in the chosen directory for the user to select."""
    videos = list(directory.glob("*.mp4")) + list(directory.glob("*.mkv")) + list(directory.glob("*.mov"))
    if not videos:
        print(f"No video files found in {directory}.")
        return None

    print(f"\n--- Video Selection in {directory.name} ---")
    for i, v in enumerate(videos, 1):
        print(f"{i}: {v.name}")

    try:
        choice = int(input(f"Select video (1-{len(videos)}): "))
        return videos[choice - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None

def extract_audio():
    # 1. Define Base Path
    source_base = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    
    # 2. Use the Interactive Picker to find the source folder
    print("Step 1: Navigate to the folder containing your source video.")
    source_folder = interactive_path_picker(source_base)
    
    # 3. Select the specific video file
    video_file = select_video_file(source_folder)
    if not video_file:
        return

    # 4. Use the Interactive Picker to choose where to save the MP3
    print("\nStep 2: Navigate to the destination folder where the MP3 should be saved.")
    destination_folder = interactive_path_picker(source_base.parent) # Starting picker from a level up
    
    output_audio = destination_folder / f"{video_file.stem}_extracted.mp3"

    # 5. FFmpeg Extraction
    print(f"\n--- Extracting Audio ---")
    print(f"Source: {video_file.name}")
    print(f"Destination: {output_audio}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_file),
        "-vn",                 # Disable video recording
        "-acodec", "libmp3lame",
        "-ab", "192k",         # Standard high-quality bitrate
        "-ar", "44100",        # Standard frequency
        str(output_audio)
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ SUCCESS: Audio saved to {output_audio}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ FFmpeg Error: {e}")

if __name__ == "__main__":
    extract_audio()