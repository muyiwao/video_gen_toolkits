import subprocess
import os
from pathlib import Path

def remove_black_background():
    # --- CONFIGURATION ---
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\attachments")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 1. Aspect Ratio Selection
    print("\n--- Aspect Ratio Selection ---")
    print("1. Vertical (9:16 - 1080x1920)")
    print("2. Horizontal (16:9 - 1920x1080)")
    ar_choice = input("Select option (1 or 2): ").strip()

    width, height = (1080, 1920) if ar_choice == '1' else (1920, 1080)
    ar_name = "9x16" if ar_choice == '1' else "16x9"

    # 2. File Selection Logic
    video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    image_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    files = [f for f in source_dir.iterdir() if f.suffix.lower() in video_exts or f.suffix.lower() in image_exts]

    if not files:
        print(f"❌ No compatible files found in {source_dir}")
        return

    print("\n--- Available Files ---")
    for idx, f in enumerate(files, 1):
        print(f"{idx}. {f.name}")
    print("A. Process All Files")

    try:
        file_choice = input("\nSelect file number or 'A': ").strip().upper()
        to_process = files if file_choice == 'A' else [files[int(file_choice)-1]]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return

    # 3. Filter Chain Logic
    # We use 'colorkey' to turn black into transparency.
    # We use 'format=rgba' to ensure the internal engine is processing 4 channels (Red, Green, Blue, Alpha).
    vf_chain = (
        f"colorkey=0x000000:0.1:0.1,"
        f"format=rgba,"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x00000000"
    )

    for item in to_process:
        ext = item.suffix.lower()
        
        if ext in video_exts:
            # SWITCHED TO .MOV (QuickTime RLE) - This is the most stable format for transparency
            output_file = dest_dir / f"{item.stem}_{ar_name}.mov"
            codec_args = [
                "-c:v", "qtrle",      # QuickTime Animation codec (Supports Alpha perfectly)
                "-pix_fmt", "argb"    # Standard pixel format for transparent MOV
            ]
        else:
            output_file = dest_dir / f"{item.stem}_{ar_name}.png"
            codec_args = ["-update", "1"]

        print(f"\n🎬 Processing: {item.name} -> {output_file.name}...")

        command = [
            "ffmpeg", "-y",
            "-i", str(item),
            "-vf", vf_chain,
            *codec_args,
            str(output_file)
        ]

        # Use stderr=subprocess.PIPE to catch errors if they happen
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Success: Saved to {output_file}")
        else:
            print(f"❌ FFmpeg Error: {result.stderr}")

    print("\n✨ Processing complete. Use VLC Player or a Video Editor to view these files.")

if __name__ == "__main__":
    remove_black_background()