import subprocess
import json
import math
from pathlib import Path

def get_audio_info(audio_path):
    """Retrieves duration and sample rate of the audio file."""
    command = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=duration,sample_rate",
        "-of", "json", str(audio_path)
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    if not data.get('streams'):
        raise ValueError("No audio stream found in the file.")
        
    duration = float(data['streams'][0]['duration'])
    return duration

def create_infinite_audio_loop():
    # 1. Paths Configuration
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\sound")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Find Audio Source (Supports mp3, wav, m4a, or extraction from mp4)
    audio_extensions = ["*.mp3", "*.wav", "*.m4a"] #, "*.mp4"]
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(list(source_dir.glob(ext)))
        
    if not audio_files:
        print(f"❌ No audio or video files found in {source_dir}")
        return
    
    audio_input = audio_files[0]
    print(f"🎵 Source detected: {audio_input.name}")

    # 3. User Input for Length
    try:
        target_hours = float(input("Enter total length needed in HOURS (e.g., 1, 8, 10): "))
        target_seconds = int(target_hours * 3600)
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    final_output = output_dir / f"Loop_{int(target_hours)}h_{audio_input.stem}.mp3"

    try:
        duration = get_audio_info(audio_input)
        
        # Calculate how many loops are needed
        # -1 means infinite, but we use a specific count to avoid file bloat
        loop_count = math.ceil(target_seconds / duration)

        print(f"🚀 Generating {target_hours} hours of audio...")
        print("This may take a moment depending on the length...")

        # FFMPEG COMMAND EXPLAINED:
        # -stream_loop: Loops the input file X times.
        # -t: Sets the exact duration limit.
        # -af "afade": We apply a very subtle 2-second fade out at the very end
        #             to ensure the long-form file doesn't end abruptly.
        
        command = [
            "ffmpeg", "-y",
            "-stream_loop", str(loop_count),
            "-i", str(audio_input),
            "-t", str(target_seconds),
            "-af", f"afade=t=out:st={target_seconds-2}:d=2",
            "-c:a", "libmp3lame",
            "-q:a", "2", # High quality VBR
            str(final_output)
        ]

        subprocess.run(command, check=True)

        print(f"\n✅ SUCCESS!")
        print(f"Output saved to: {final_output}")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    create_infinite_audio_loop()