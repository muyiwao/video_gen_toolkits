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

    file_choice = input("\nSelect file number or 'A': ").strip().upper()
    
    to_process = files if file_choice == 'A' else [files[int(file_choice)-1]]

    # 3. Filter Chain
    # colorkey removes black, scale fits the frame, pad centers it with transparency
    vf_chain = (
        f"colorkey=0x000000:0.1:0.1,"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x00000000"
    )

    for item in to_process:
        ext = item.suffix.lower()
        
        if ext in video_exts:
            # Outputting as .mp4 using HEVC with Alpha support
            output_file = dest_dir / f"{item.stem}_{ar_name}.mp4"
            # libx265 with pixel format yuva420p allows transparency in mp4
            codec_args = ["-c:v", "libx265", "-pix_fmt", "yuva420p", "-tag:v", "hvc1"]
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

        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        if result.returncode == 0:
            print(f"✅ Success: Saved to {dest_dir}")
        else:
            print(f"❌ Error: {result.stderr.decode('utf-8')}")

    print("\n✨ Processing complete.")

if __name__ == "__main__":
    remove_black_background()