import subprocess
import os
from pathlib import Path

# --- CONFIGURATION ---
BASE_PATH = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content")
VIDEO_FOLDER = BASE_PATH / "raw_lessons"
ASSET_DIR = BASE_PATH / "attachments" / "long"
OUTPUT_DIR = BASE_PATH / "output" / "long_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Assets
V1 = ASSET_DIR / "intro_video.mp4"
V2 = ASSET_DIR / "subscribe-cta.mp4"
V3 = ASSET_DIR / "outtro_video.mp4"
IMAGE_1 = ASSET_DIR / "background_with_logo.png"

OUTPUT_FILE = OUTPUT_DIR / "final_math_lesson_long.mp4"
TEMP_DIR = BASE_PATH / "temp_segments"
TEMP_DIR.mkdir(exist_ok=True)

def generate_number_video(number, output_path):
    """Generates a 2-second clip with a centered number and silent audio."""
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=2",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-vf", f"drawtext=text='{number}':fontcolor=white:fontsize=200:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def create_full_video():
    lesson_segments = []

    print("🔢 Generating number intros (1-20)...")
    for i in range(1, 21):
        vid_path = VIDEO_FOLDER / f"{i}.mp4"
        if vid_path.exists():
            num_path = TEMP_DIR / f"num_{i}.mp4"
            generate_number_video(i, num_path)
            lesson_segments.append(num_path)
            lesson_segments.append(vid_path)

    if not lesson_segments:
        print("❌ No lesson videos found in the source folder.")
        return

    # 1. Merge all lessons into one temp file
    concat_list = BASE_PATH / "temp_list.txt"
    with open(concat_list, "w") as f:
        for file in lesson_segments:
            f.write(f"file '{file.resolve()}'\n")

    temp_main_lesson = BASE_PATH / "temp_main_combined.mp4"
    print("⚡ Step 1: Merging segments into master lesson...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-af", "aresample=async=1", "-c:a", "aac", str(temp_main_lesson)
    ], check=True)

    # 2. Final Filter Graph
    print("🚀 Step 2: Applying Background, Chroma Key, and Overlays...")
    
    # filter_complex breakdown:
    # [0:v] Image 1 (Background)
    # [1:v] Main combined video (Chroma keying black to transparent)
    # [2:v] Subscribe CTA (Overlayed every 30s)
    # [3:v] Intro Video (Beginning)
    # [4:v] Outro Video (End)
    
    filter_complex = (
        "[0:v]scale=1280:720,setsar=1[bg]; "
        "[1:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
        "colorkey=0x000000:0.1:0.1,setsar=1[lesson_transparent]; "
        "[2:v]scale=350:-1[cta]; "
        "[3:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1[intro_v]; "
        "[4:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1[outro_v]; "
        
        "[bg][lesson_transparent]overlay=format=auto:shortest=1[main_bg_v]; "
        "[main_bg_v][cta]overlay=W-w-20:H-h-20:enable='lt(mod(t,30),5)'[main_final_v]; "
        
        "[intro_v][3:a][main_final_v][1:a][outro_v][4:a]concat=n=3:v=1:a=1[v][a]"
    )

    final_cmd = [
        "ffmpeg", "-y",
        "-i", str(IMAGE_1),            # [0]
        "-i", str(temp_main_lesson),    # [1]
        "-i", str(V2),                 # [2]
        "-i", str(V1),                 # [3]
        "-i", str(V3),                 # [4]
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-ar", "48000", 
        "-ac", "2",                     # FIXED: Now a string "2"
        str(OUTPUT_FILE)
    ]

    try:
        subprocess.run(final_cmd, check=True)
        print(f"✨ Process Complete! Video saved: {OUTPUT_FILE}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Error: {e}")
    finally:
        # Cleanup
        for f in TEMP_DIR.glob("*.mp4"): 
            try: os.remove(f)
            except: pass
        if concat_list.exists(): os.remove(concat_list)
        if temp_main_lesson.exists(): os.remove(temp_main_lesson)

if __name__ == "__main__":
    create_full_video()