import subprocess
from pathlib import Path
import shutil
import json

# --- GLOBAL CONFIGURATION ---
BASE_PATH = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
OUTPUT_DIR = BASE_PATH / "output" / "output_long"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAIN_VIDEO = BASE_PATH / "edu_content" / "raw_lessons" / "merged_output.mp4"
OUTPUT_FILE = OUTPUT_DIR / "final_edited_video.mp4"

def get_video_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(json.loads(result.stdout)["format"]["duration"])

def get_encoder():
    if shutil.which("nvidia-smi"):
        return "h264_nvenc"
    return "libx264"

def get_deep_voice_filter(speed):
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
    speed = float(input("⏩ Video Speed (default 1.0): ") or 1.0)

    image_bg = asset_dir / "background_with_logo.png"
    v_intro = asset_dir / "intro_video.mp4"
    v_cta_img = asset_dir / "subscribe-cta.png"
    v_outro = asset_dir / "outtro_video.mp4"

    assets = [MAIN_VIDEO, image_bg, v_intro, v_cta_img, v_outro]
    if not all(f.exists() for f in assets):
        missing = [str(f) for f in assets if not f.exists()]
        print(f"❌ Missing files: {missing}")
        return

    duration = get_video_duration(MAIN_VIDEO)
    encoder = get_encoder()
    pts_val = 1.0 / speed
    audio_filter = get_deep_voice_filter(speed)

    # --- UPDATED FILTERGRAPH ---
    # Fix: replaced 'and(x,y)' with '(x)*(y)'
    # (gt(t,30)) -> must be after 30 seconds
    # (lt(mod(t,30),5)) -> must be in the first 5 seconds of the 30-second loop
    enable_logic = "gte(t,30)*lt(mod(t,30),5)"

    filter_complex = (
        f"[2:v]colorkey=0x000000:0.1:0.1,setpts={pts_val}*PTS[vid];"
        f"[2:a]{audio_filter}[aud];"
        "[1:v][vid]overlay=shortest=1[tmp];"
        f"[tmp][3:v]overlay=W-w-20:H-h-20:enable='{enable_logic}'[lesson];"
        "[0:v][0:a][lesson][aud][4:v][4:a]concat=n=3:v=1:a=1[v][a]"
    )

    print(f"🚀 Rendering: CTA appears every 30s starting at 00:30...")

    cmd = [
        "ffmpeg", "-y",
        "-threads", "0",
        "-i", str(v_intro),
        "-loop", "1", "-t", str(duration * pts_val + 60), "-i", str(image_bg),
        "-i", str(MAIN_VIDEO),
        "-loop", "1", "-t", str(duration * pts_val + 60), "-i", str(v_cta_img),
        "-i", str(v_outro),
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", encoder,
        "-preset", "ultrafast",
        "-crf", "24",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(OUTPUT_FILE)
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"✨ SUCCESS: {OUTPUT_FILE}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Render failed: {e}")

if __name__ == "__main__":
    edit_long_video()