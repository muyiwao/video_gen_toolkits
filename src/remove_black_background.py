import subprocess
import os
from pathlib import Path

def remove_black_background():
    # --- CONFIGURATION ---
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\raw_lessons")
    
    # Ensure destination exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Supported extensions
    video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    image_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

    # 1. Gather all files
    all_files = [f for f in source_dir.iterdir() if f.suffix.lower() in video_exts or f.suffix.lower() in image_exts]

    if not all_files:
        print(f"❌ No compatible images or videos found in {source_dir}")
        return

    print(f"🚀 Found {len(all_files)} files. Starting background removal...")

    for item in all_files:
        ext = item.suffix.lower()
        
        # We use item.name to keep the filename identical.
        # Note: Videos MUST be .mov and Images MUST be .png to support transparency.
        # If the input is already .mov or .png, the name remains 100% identical.
        if ext in video_exts:
            output_file = dest_dir / f"{item.stem}.mov"
            codec_args = ["-c:v", "png", "-pix_fmt", "rgba"] 
        else:
            output_file = dest_dir / f"{item.stem}.png"
            codec_args = ["-update", "1"] 

        print(f"🎬 Processing: {item.name} -> {output_file.name}...")

        # --- FFmpeg Command ---
        command = [
            "ffmpeg", "-y",
            "-i", str(item),
            "-vf", "colorkey=0x000000:0.1:0.1",
            *codec_args,
            str(output_file)
        ]

        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        if result.returncode == 0:
            print(f"✅ Success: {output_file.name}")
        else:
            print(f"❌ Error processing {item.name}: {result.stderr.decode('utf-8')}")

    print("\n✨ Batch processing complete.")

if __name__ == "__main__":
    remove_black_background()