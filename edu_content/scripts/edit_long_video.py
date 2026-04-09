import subprocess
import os
from pathlib import Path

# --- CONFIGURATION ---
BASE_PATH = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
ASSET_DIR = BASE_PATH / "math_content" / "attachments" / "long"
OUTPUT_DIR = BASE_PATH / "output" / "output_long"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Main Video Input (Update this to your specific filename)
MAIN_VIDEO = BASE_PATH / "math_content" / "raw_lessons" / "merged_output.mp4" 

# Assets
IMAGE_1 = ASSET_DIR / "background_with_logo.png"
V1 = ASSET_DIR / "intro_video.mp4"         # Video 1: Intro
V2 = ASSET_DIR / "subscribe-cta.mp4"      # Video 2: 30s Overlay
V3 = ASSET_DIR / "outtro_video.mp4"       # Video 3: Outro

OUTPUT_FILE = OUTPUT_DIR / "final_edited_video.mp4"

def edit_long_video():
    if not MAIN_VIDEO.exists():
        print(f"❌ Error: Main video not found at {MAIN_VIDEO}")
        return

    print("🚀 Starting Video Edit: Applying Chroma Key and Overlays...")

    # FILTER GRAPH BREAKDOWN:
    # [0:v] Image 1: Looped, scaled to fill 16:9, and cropped.
    # [1:v] Main Video: Chroma keyed (black removed) and padded.
    # [2:v] Video 2: CTA scaled.
    # [3:v] Video 1: Intro scaled.
    # [4:v] Video 3: Outro scaled.
    
    filter_complex = (
        # 1. Prep Background (Fill screen)
        "[0:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1[bg]; "
        
        # 2. Prep Main Video (Remove Black Background)
        # colorkey=color:similarity:blend
        "[1:v]colorkey=0x000000:0.1:0.1,scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[main_transp]; "
        
        # 3. Prep Assets
        "[2:v]scale=350:-1[cta]; "
        "[3:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1[intro_v]; "
        "[4:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1[outro_v]; "
        
        # 4. Layering: Image 1 -> Main Video -> CTA Overlay
        "[bg][main_transp]overlay=format=auto:shortest=1[v_with_bg]; "
        "[v_with_bg][cta]overlay=W-w-20:H-h-20:enable='lt(mod(t,30),5)'[main_final_v]; "
        
        # 5. Concatenation: Intro -> Main Content -> Outro
        "[intro_v][3:a][main_final_v][1:a][outro_v][4:a]concat=n=3:v=1:a=1[v][a]"
    )

    final_cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(IMAGE_1),  # [0] Loop Image 1
        "-i", str(MAIN_VIDEO),             # [1]
        "-i", str(V2),                     # [2]
        "-i", str(V1),                     # [3]
        "-i", str(V3),                     # [4]
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", 
        "-preset", "medium", 
        "-crf", "18", 
        "-c:a", "aac", 
        "-ac", "2", 
        "-ar", "48000",
        str(OUTPUT_FILE)
    ]

    try:
        subprocess.run(final_cmd, check=True)
        print(f"✨ SUCCESS: Video saved to {OUTPUT_FILE}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Error: {e}")

if __name__ == "__main__":
    edit_long_video()