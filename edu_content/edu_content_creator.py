import subprocess
import os
import json
import re
import shutil
from pathlib import Path
import sys

# Adds the project root to the python path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from edu_content.scripts import generate_thumbnail

# --- CONFIGURATION ---
BASE_PATH = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
MAIN_V_DIR = BASE_PATH / "edu_content" / "raw_lessons"
JSON_METADATA_PATH = BASE_PATH / "input" / "metadata.json"

# --- SHARED UTILITIES ---
def sanitize_filename(name):
    """Removes illegal characters and spaces for clean OS filenames."""
    clean = re.sub(r'[\\/*?:"<>|√=+\-]', '', name)
    return clean.replace(' ', '_').strip('_')

def get_duration(filename):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(filename)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except:
        return 0.0

def get_encoder():
    """Detects GPU for faster rendering on Long videos."""
    return "h264_nvenc" if shutil.which("nvidia-smi") else "libx264"

def get_deep_voice_filter(speed):
    pitch_factor = 0.85 
    tempo_correction = 1.0 / pitch_factor 
    final_tempo = tempo_correction * speed
    return (
        f"asetrate=44100*{pitch_factor},atempo={final_tempo},"
        f"equalizer=f=250:width_type=h:w=100:g=3," 
        f"equalizer=f=3000:width_type=h:w=200:g=5,"
        f"compand=attacks=0:points=-80/-80|-20/-5|-10/-2|0/-1"
    )

# --- PROCESSING ENGINES ---
def run_long_editor(category, speed):
    """Processes a single long-form educational video."""
    output_dir = BASE_PATH / "output" / "output_long"
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = BASE_PATH / "edu_content" / "attachments" / category / "long"
    output_file = output_dir / "final_edited_video.mp4"
    main_video = MAIN_V_DIR / "merged_output.mp4"

    if not main_video.exists():
        print(f"❌ Error: {main_video} not found.")
        return

    assets = {
        "bg": asset_dir / "background_with_logo.png",
        "intro": asset_dir / "intro_video.mp4",
        "cta": asset_dir / "subscribe-cta.png",
        "outro": asset_dir / "outtro_video.mp4"
    }

    duration = get_duration(main_video)
    pts_val = 1.0 / speed
    audio_filter = get_deep_voice_filter(speed)
    enable_logic = "gte(t,30)*lt(mod(t,30),5)"

    filter_complex = (
        f"[2:v]colorkey=0x000000:0.1:0.1,setpts={pts_val}*PTS[vid];"
        f"[2:a]{audio_filter}[aud];"
        "[1:v][vid]overlay=shortest=1[tmp];"
        f"[tmp][3:v]overlay=W-w-20:H-h-20:enable='{enable_logic}'[lesson];"
        "[0:v][0:a][lesson][aud][4:v][4:a]concat=n=3:v=1:a=1[v][a]"
    )

    cmd = [
        "ffmpeg", "-y", "-i", str(assets["intro"]),
        "-loop", "1", "-t", str(duration * pts_val + 60), "-i", str(assets["bg"]),
        "-i", str(main_video),
        "-loop", "1", "-t", str(duration * pts_val + 60), "-i", str(assets["cta"]),
        "-i", str(assets["outro"]),
        "-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]",
        "-c:v", get_encoder(), "-preset", "ultrafast", "-crf", "23", str(output_file)
    ]
    
    print(f"🚀 Rendering Long Video ({category})...")
    subprocess.run(cmd, check=True)
    print(f"✨ SUCCESS: {output_file}")

def run_shorts_batch(category, speed, caption, scale):
    """Processes batch shorts and exports matching JSON metadata for thumbnails."""
    output_dir = BASE_PATH / "output" / "output_shorts"
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = BASE_PATH / "edu_content" / "attachments" / category / "shorts"
    
    # Theme Logic
    colors = {"box": "red", "text": "white"} if category == "math" else {"box": "0x00ffff", "text": "black"}
    
    paths = {
        "v1": asset_dir / "intro_video.mp4",
        "v2": asset_dir / "subscribe-cta.mp4",
        "v3": asset_dir / "outtro_video.mp4",
        "img1": asset_dir / "background_with_logo.png",
        "img2": asset_dir / "related_video_pointer.png"
    }

    if not JSON_METADATA_PATH.exists():
        print("❌ Error: metadata.json missing.")
        return

    with open(JSON_METADATA_PATH, 'r', encoding='utf-8') as f:
        master_metadata = json.load(f)

    raw_videos = sorted([f for f in MAIN_V_DIR.iterdir() if f.suffix.lower() == ".mp4"], key=os.path.getctime)

    print(f"\n🚀 Starting Shorts Batch: {len(raw_videos)} videos found.")

    for video_path, seo_package in zip(raw_videos, master_metadata):
        raw_title = seo_package.get("title", "Untitled")
        safe_name = sanitize_filename(raw_title)
        
        out_v = output_dir / f"{safe_name}.mp4"
        out_j = output_dir / f"{safe_name}.json" # For Thumbnail/Upload use
        
        W, H = 1080, 1920
        target_w = int(W * (scale / 100))
        pts_val = 1.0 / speed
        
        # Calculate timing for caption
        d_intro = get_duration(paths["v1"])
        d_main = get_duration(video_path) / speed
        d_outro = get_duration(paths["v3"])
        total_d = d_intro + d_main + d_outro
        cap_end = max(0, total_d - 12)
        
        clean_cap = caption.replace(":", "\\:").replace("'", "").replace("%", "\\%")
        
        drawtext = (
            f"drawtext=text='{clean_cap}':fontcolor={colors['text']}:fontsize=60:font='Arial':"
            f"box=1:boxcolor={colors['box']}@1.0:boxborderw=25:x=(w-text_w)/2:y=250:enable='lt(t,{cap_end:.2f})'"
        )

        filter_complex = (
            f"[4:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[bg];"
            f"[0:v]scale={target_w}:-1,setpts={pts_val:.4f}*PTS,colorkey=0x000000:0.1:0.1[main_v_key];"
            f"[0:a]{get_deep_voice_filter(speed)}[main_a_processed];" 
            f"[bg][main_v_key]overlay=x=(W-w)/2:y=(H-h)/2[base];"
            f"[base]{drawtext}[with_caption];"
            f"[2:v]scale={W}:-1[cta_v];"
            f"[with_caption][cta_v]overlay=0:(H-h)/2:enable='lt(mod(t,30),3)'[with_cta];"
            f"[5:v]scale=1000:-1[ptr];"
            f"[with_cta][ptr]overlay=x=(W-w)/2:y=H-h:enable='gt(t,10)'[lesson_v];"
            f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[v1_f];"
            f"[3:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[v3_f];"
            f"[v1_f][1:a][lesson_v][main_a_processed][v3_f][3:a]concat=n=3:v=1:a=1[v_out][a_out]"
        )

        cmd = [
            'ffmpeg', '-y', '-i', str(video_path), '-i', str(paths["v1"]), '-i', str(paths["v2"]),
            '-i', str(paths["v3"]), '-i', str(paths["img1"]), '-i', str(paths["img2"]),
            '-filter_complex', filter_complex, '-map', '[v_out]', '-map', '[a_out]',
            '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', str(out_v)
        ]

        try:
            print(f"🎬 Processing: {video_path.name} -> {safe_name}.mp4")
            subprocess.run(cmd, check=True, capture_output=True)
            
            # --- METADATA EXPORT ---
            with open(out_j, 'w', encoding='utf-8') as jf:
                json.dump(seo_package, jf, indent=4)
                
            print(f"✅ Success: Video and Metadata saved for '{raw_title}'")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg Error on {video_path.name}: {e.stderr.decode()}")

# --- MAIN INTERFACE ---
if __name__ == "__main__":
    print("====================================")
    print("   EDUCATION VIDEO PRODUCTION ENGINE")
    print("====================================")
    
    mode = input("🎬 Select Mode (1. Shorts Batch | 2. Long Video): ").strip()
    cat = input("📂 Category (math/science): ").strip().lower()
    
    if cat not in ['math', 'science']:
        print("❌ Invalid category. Exiting.")
        exit()

    spd = float(input("⏩ Video Speed (default 1.0): ") or 1.0)

    if mode == "1":
        cap = input("💬 Global Caption: ").strip()
        scl = float(input("📏 Text Scale (default 100): ") or 100)
        run_shorts_batch(cat, spd, cap, scl)
    else:
        run_long_editor(cat, spd)
        generate_thumbnail.generate_thumbnail_with_caption()

    
    print("\n✨ Processing Complete.")