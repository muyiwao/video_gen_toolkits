import subprocess
import os
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
BASE_PATH = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
OUTPUT_DIR = BASE_PATH / "output" / "output_long"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAIN_VIDEO = BASE_PATH / "edu_content" / "raw_lessons" / "merged_output.mp4" 
OUTPUT_FILE = OUTPUT_DIR / "final_edited_video.mp4"

def get_deep_voice_filter(speed):
    """Calculates pitch shift and tempo correction for a deep voice effect."""
    pitch_factor = 0.85 
    tempo_correction = 1.0 / pitch_factor 
    final_tempo = tempo_correction * speed

    return (
        f"asetrate=44100*{pitch_factor},atempo={final_tempo},"
        f"equalizer=f=250:w=100:g=3,equalizer=f=3000:w=200:g=5,"
        f"compand=attacks=0:points=-80/-80|-20/-5|-10/-2|0/-1"
    )

def get_asset_paths():
    while True:
        choice = input("📂 Enter category (math/science): ").strip().lower()
        if choice in ['math', 'science']:
            return BASE_PATH / "edu_content" / "attachments" / choice / "long"
        print("⚠️ Invalid choice.")

def edit_long_video():
    asset_dir = get_asset_paths()
    u_speed = float(input("⏩ Video Speed (default 1.0): ") or 1.0)
    
    # Asset definition
    image_bg = asset_dir / "background_with_logo.png"
    v_intro = asset_dir / "intro_video.mp4"      
    v_cta_img = asset_dir / "subscribe-cta.png"    
    v_outro = asset_dir / "outtro_video.mp4"     

    # Validation
    assets = [MAIN_VIDEO, image_bg, v_intro, v_cta_img, v_outro]
    if not all(f.exists() for f in assets):
        missing = [str(f) for f in assets if not f.exists()]
        print(f"❌ Error: Missing files: {missing}")
        return

    pts_val = 1.0 / u_speed
    audio_filter = get_deep_voice_filter(u_speed)

    # --- OPTIMIZED FILTERGRAPH ---
    # Since all inputs are 1280x720, we remove scale/setsar from everything except the CTA overlay.
    filter_complex = (
        # 1. Scale CTA only (keep it as a small overlay)
        f"[3:v]scale=350:-1[cta]; "
        # 2. Process Lesson Speed
        f"[2:v]colorkey=0x000000:0.1:0.1,setpts={pts_val:.4f}*PTS[main_v]; "
        # 3. Apply Audio Filter
        f"[2:a]{audio_filter}[lesson_a]; "
        # 4. Overlay sequence: BG -> Lesson -> CTA
        f"[1:v][main_v]overlay=shortest=1[ov1]; "
        f"[ov1][cta]overlay=W-w-20:H-h-20:enable='lt(t,15)'[lesson_v]; "
        # 5. Final Concat of Intro + Lesson + Outro
        f"[0:v][0:a][lesson_v][lesson_a][4:v][4:a]concat=n=3:v=1:a=1[v][a]"
    )

    print("🚀 Rendering 720p native output...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(v_intro),                 # Input 0
        "-loop", "1", "-i", str(image_bg),  # Input 1
        "-i", str(MAIN_VIDEO),               # Input 2
        "-loop", "1", "-i", str(v_cta_img),  # Input 3
        "-i", str(v_outro),                 # Input 4
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", 
        "-preset", "veryfast", 
        "-crf", "22", 
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(OUTPUT_FILE)
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✨ SUCCESS: {OUTPUT_FILE}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during rendering: {e}")

if __name__ == "__main__":
    edit_long_video()