import subprocess
from pathlib import Path

def select_raw_video(directory):
    """Allows user to select a video file from the raw folder at runtime."""
    video_extensions = (".mp4", ".mov", ".mkv", ".avi")
    files = sorted([f for f in directory.glob("*") if f.suffix.lower() in video_extensions])
    
    if not files:
        print(f"❌ No video files found in: {directory}")
        return None

    print("\n--- Available Raw Video Footage ---")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file.name}")
    
    try:
        choice = int(input(f"\nSelect video to enhance (1-{len(files)}): "))
        if 1 <= choice <= len(files):
            return files[choice - 1]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
    return None

def enhance_rain_atmosphere():
    # 1. Path Configuration
    raw_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw")
    enhanced_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    
    # Ensure destination exists
    enhanced_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Runtime Selection
    input_video = select_raw_video(raw_dir)
    if not input_video:
        return

    # Set destination path
    output_path = enhanced_dir / f"Enhanced_{input_video.name}"

    # 3. Atmospheric Filter (Requirement 3 & 4)
    # Focus: Payne's Gray, Ultramarine, and Muted Violets
    # Logic: Static footage, high contrast, moody depth for sleep-friendly visuals.
    color_grading = (
        "colorchannelmixer="
        ".75:.1:.1:0: "   # Muting Reds for Payne's Gray base
        "0:.85:.2:0: "    # Deepening Greens
        "0:.25:1.25:0, "  # Boosting Blues for Ultramarine/Violets
        "eq=brightness=-0.06:contrast=1.2:saturation=0.8, "
        "unsharp=5:5:0.7:5:5:0.0"
    )

    # 4. FFmpeg Execution
    print(f"\n✨ Processing: {input_video.name}")
    print(f"🎨 Applying: Deep Relaxation & Moody Color Profile...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_video),
        "-vf", color_grading,
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ SUCCESS! Cinematic footage saved to:")
        print(f"👉 {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during enhancement: {e}")

if __name__ == "__main__":
    enhance_rain_atmosphere()