import subprocess
import os
import json
import re
from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
BASE_PATH = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
ASSET_DIR = BASE_PATH / "math_content" / "attachments" / "shorts"
MAIN_V_DIR = BASE_PATH / "math_content" / "raw_lessons"
OUTPUT_DIR = BASE_PATH / "output" / "output_shorts"
JSON_METADATA_PATH = BASE_PATH / "input" / "metadata.json"

PATHS = {
    "v1":   str(ASSET_DIR / "intro_video.mp4"),
    "v2":   str(ASSET_DIR / "subscribe-cta.mp4"),
    "v3":   str(ASSET_DIR / "outtro_video.mp4"),
    "img1": str(ASSET_DIR / "background_with_logo.png"),
    "img2": str(ASSET_DIR / "related_video_pointer.png"),
}

def sanitize_filename(name):
    clean = re.sub(r'[\\/*?:"<>|√=+\-]', '', name)
    return clean.replace(' ', '_').strip('_')

def get_duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return float(result.stdout)

def get_deep_voice_filter(speed):
    """
    Creates a filter chain for a deep, clear male voice.
    - Pitch shift down (0.85 rate)
    - Tempo correction to maintain original speed
    - Compand for loudness and clarity
    - High pass to remove 'mumble' bass
    """
    # Base pitch shift (lower value = deeper)
    pitch_factor = 0.85 
    # Correct the speed changed by pitch shift
    tempo_correction = 1.0 / pitch_factor 
    # Combine with user-defined speed
    final_tempo = tempo_correction * speed

    # Filter Chain:
    # 1. asetrate: Lowers pitch but slows down audio
    # 2. atempo: Speeds it back up to the desired rate
    # 3. equalizer: Boosts 250Hz for 'body', 3kHz for 'clarity'
    # 4. compand: Acts as a compressor/limiter to make it LOUD and consistent
    voice_chain = (
        f"asetrate=44100*{pitch_factor},"
        f"atempo={final_tempo},"
        f"equalizer=f=250:width_type=h:w=100:g=3," 
        f"equalizer=f=3000:width_type=h:w=200:g=5,"
        f"compand=attacks=0:points=-80/-80|-20/-5|-10/-2|0/-1"
    )
    return voice_chain

def build_ffmpeg_command(main_v_path, output_path, caption_text, text_scale=100, speed=1.0):
    W, H = 1080, 1920
    target_width = int(W * (text_scale / 100))
    video_pts = 1.0 / speed
    
    # NEW: Voice processing chain
    audio_processing = get_deep_voice_filter(speed)

    d_intro = get_duration(PATHS["v1"])
    d_main_raw = get_duration(main_v_path)
    d_outro = get_duration(PATHS["v3"])
    
    d_main_final = d_main_raw / speed
    total_duration = d_intro + d_main_final + d_outro
    caption_end_time = max(0, total_duration - 12)

    clean_caption = caption_text.replace(":", "\\:").replace("'", "").replace("%", "\\%")

    drawtext_filter = (
        f"drawtext=text='{clean_caption}':fontcolor=white:fontsize=60:font='Arial':"
        f"box=1:boxcolor=red@1.0:boxborderw=25:"
        f"x=(w-text_w)/2:y=250:enable='lt(t,{caption_end_time:.2f})'" 
    )

    filter_complex = (
        # Video Background & Main Logic
        f"[4:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[bg];"
        f"[0:v]scale={target_width}:-1,setpts={video_pts:.4f}*PTS,colorkey=0x000000:0.1:0.1[main_v_key];"
        
        # Audio Deep Voice Processing
        f"[0:a]{audio_processing}[main_a_processed];" 
        
        f"[bg][main_v_key]overlay=x=(W-w)/2:y=(H-h)/2[base];"
        f"[base]{drawtext_filter}[with_caption];"
        f"[2:v]scale={W}:-1[cta_v];"
        f"[with_caption][cta_v]overlay=0:(H-h)/2:enable='lt(mod(t,30),3)'[with_cta];"
        f"[5:v]scale=1000:-1[ptr];"
        f"[with_cta][ptr]overlay=x=(W-w)/2:y=H-h:enable='gt(t,10)'[lesson_final_v];"
        f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[v1_f];"
        f"[3:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[v3_f];"
        
        # Concat everything
        f"[v1_f][1:a][lesson_final_v][main_a_processed][v3_f][3:a]concat=n=3:v=1:a=1[v_out][a_out]"
    )

    return [
        'ffmpeg', '-y',
        '-i', main_v_path, '-i', PATHS["v1"], '-i', PATHS["v2"],
        '-i', PATHS["v3"], '-i', PATHS["img1"], '-i', PATHS["img2"],
        '-filter_complex', filter_complex, '-map', '[v_out]', '-map', '[a_out]',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '192k', output_path
    ]

if __name__ == "__main__":
    if not JSON_METADATA_PATH.exists():
        print(f"❌ Metadata JSON not found.")
        exit()
    with open(JSON_METADATA_PATH, 'r', encoding='utf-8') as f:
        master_metadata = json.load(f)

    raw_videos = [f for f in MAIN_V_DIR.iterdir() if f.suffix.lower() == ".mp4"]
    raw_videos.sort(key=lambda x: os.path.getctime(x))

    print("\n🚀 --- Deep Voice Batch Processing ---")
    u_caption = input("💬 Global Caption: ").strip()
    u_scale = float(input("📏 Main Text Scale (default 100): ") or 100)
    u_speed = float(input("⏩ Video Speed (default 1.0): ") or 1.0)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for video_path, seo_package in zip(raw_videos, master_metadata):
        raw_title = seo_package.get("title", "Untitled")
        safe_name = sanitize_filename(raw_title)
        v_out_p = os.path.join(OUTPUT_DIR, f"{safe_name}.mp4")
        j_out_p = os.path.join(OUTPUT_DIR, f"{safe_name}.json")

        print(f"\n🎬 Voice Processing: {video_path.name}...")
        
        try:
            cmd = build_ffmpeg_command(str(video_path), v_out_p, u_caption, u_scale, u_speed)
            subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
            
            with open(j_out_p, 'w', encoding='utf-8') as jf:
                json.dump(seo_package, jf, indent=4)
            print(f"✅ Success: {safe_name}.mp4")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e.stderr}")

    print("\n✨ All videos processed with deep voice.")