import os
import subprocess
import json
import glob
import re
from datetime import timedelta
from pathlib import Path

def format_timestamp(seconds):
    """Converts seconds into a [MM:SS] format."""
    td = timedelta(seconds=seconds)
    minutes, seconds_div = divmod(td.seconds, 60)
    return f"[{minutes:02d}:{seconds_div:02d}]"

def download_transcript():
    video_url = input("🔗 Enter the YouTube URL (Scheduled/Private/Public): ").strip()
    if not video_url:
        return

    output_txt = "youtube_transcript.txt"
    cookie_file = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\reaction_content\cookies.txt")

    # --- UPDATED COMMAND: Removed strict --sub-format json3 ---
    cmd = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--skip-download",
        "--write-auto-subs",   # Essential for scheduled videos
        "--write-subs",
        "--output", "temp_transcript",
        video_url
    ]

    if cookie_file.exists():
        print(f"📂 Using Cookies: {cookie_file}")
        cmd.extend(["--cookies", str(cookie_file)])
    else:
        print("⚠️ No cookies.txt found. Trying browser...")
        cmd.extend(["--cookies-from-browser", "chrome"])

    try:
        print("⏳ Fetching transcript data (Checking all available formats)...")
        subprocess.run(cmd, check=True)
        
        # 1. Try to find a JSON3 file first (best for our parser)
        json_files = glob.glob("temp_transcript*.json3")
        
        if json_files:
            process_json3(json_files[0], output_txt)
        else:
            # 2. Fallback: Look for VTT files (very common for auto-subs)
            vtt_files = glob.glob("temp_transcript*.vtt")
            if vtt_files:
                process_vtt(vtt_files[0], output_txt)
            else:
                print("❌ No transcript files (.json3 or .vtt) were generated.")
                print("Tip: Check if 'Captions' are available in the video settings on YouTube.")
                return

        # Cleanup
        for f in glob.glob("temp_transcript*"):
            os.remove(f)
        
        print(f"✅ Success! Saved to: {os.path.abspath(output_txt)}")

    except subprocess.CalledProcessError:
        print("\n❌ yt-dlp failed. The video may not have auto-captions generated yet.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def process_json3(file_path, output_path):
    """Parses YouTube's JSON3 format."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lines = []
    for event in data.get('events', []):
        if 'segs' in event:
            start_ms = event.get('tStartMs', 0)
            timestamp = format_timestamp(start_ms / 1000)
            text = "".join([seg['utf8'] for seg in event['segs'] if 'utf8' in seg]).strip()
            text = " ".join(text.split())
            if text:
                lines.append(f"{timestamp} {text}")
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))

def process_vtt(file_path, output_path):
    """Simple parser for VTT format if JSON3 is missing."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find timestamps and text
    lines = []
    blocks = content.split('\n\n')
    for block in blocks:
        match = re.search(r'(\d{2}:\d{2}:\d{2}.\d{3}) -->', block)
        if match:
            # Clean VTT tags like <c> or 📥
            text = re.sub(r'<[^>]+>', '', block.split('\n')[-1]).strip()
            if text:
                # Convert 00:00:05.123 to [00:05]
                time_parts = match.group(1).split(':')
                timestamp = f"[{time_parts[1]}:{time_parts[2][:2]}]"
                lines.append(f"{timestamp} {text}")
    
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))

if __name__ == "__main__":
    download_transcript()

# https://youtu.be/3IcuLn_Aul8