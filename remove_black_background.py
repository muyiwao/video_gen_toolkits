import subprocess
import os
from pathlib import Path

def remove_black_background():
    # --- CONFIGURATION ---
    # Update these placeholders to your actual folder paths
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\attachments")
    
    # Ensure destination exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Supported extensionss
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
        # Output is ALWAYS .mov (for video) or .png (for images) to support transparency
        if ext in video_exts:
            output_file = dest_dir / f"{item.stem}_transparent.mov"
            codec_args = ["-c:v", "png", "-pix_fmt", "rgba"] # High-quality transparency codec
        else:
            output_file = dest_dir / f"{item.stem}_transparent.png"
            codec_args = ["-update", "1"] # Ensure image output is handled correctly

        print(f"🎬 Processing: {item.name}...")

        # --- FFmpeg Command ---
        # colorkey=0x000000:0.1:0.1
        # 0x000000 = Black
        # 0.1 = Similarity (how close to black)
        # 0.1 = Blend (smoothness of the edges)
        command = [
            "ffmpeg", "-y",
            "-i", str(item),
            "-vf", "colorkey=0x000000:0.1:0.1",
            *codec_args,
            str(output_file)
        ]

        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        if result.returncode == 0:
            print(f"✅ Saved to: {output_file.name}")
        else:
            print(f"❌ Error processing {item.name}: {result.stderr.decode('utf-8')}")

    print("\n✨ Batch processing complete.")

if __name__ == "__main__":
    remove_black_background()