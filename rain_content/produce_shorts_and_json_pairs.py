import subprocess
import json
import re
from pathlib import Path

# --- Configuration ---
BASE_PATH = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
VIDEO_INPUT = BASE_PATH / "input" / "video_pools"
AUDIO_INPUT = BASE_PATH / "input" / "audio_pools"
JSON_METADATA = BASE_PATH / "input" / "metadata.json"

ASSET_DIR = BASE_PATH / "rain_content" / "attachments" / "shorts"
LOGO_CTA = ASSET_DIR / "logo-cta.png"
SUB_CTA = ASSET_DIR / "subscribe-cta.png"
OUTPUT_DIR = BASE_PATH / "output" / "output_shorts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_FILTERS = [
    "lowpass=f=3500", "aecho=0.8:0.88:40:0.3", 
    "bass=g=5:f=110:w=0.6", "equalizer=f=1000:width_type=h:width=200:g=-5"
]

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name).replace(' ', '_')

def produce_synced_shorts():
    if not JSON_METADATA.exists():
        print(f"❌ Master JSON not found at {JSON_METADATA}")
        return
    
    with open(JSON_METADATA, 'r', encoding='utf-8') as f:
        master_metadata = json.load(f)

    video_files = sorted(list(VIDEO_INPUT.glob("*.mp4")))
    audio_files = sorted(list(AUDIO_INPUT.glob("*.mp3")))

    if len(video_files) < 4 or len(audio_files) < 4:
        print("❌ Error: Missing assets in pools.")
        return

    short_count = 0
    font_path = "C\\:/Windows/Fonts/arialbd.ttf"
    t_w, t_h = 1080, 1920

    for i in range(4):
        video_path = video_files[i]
        audio_path = audio_files[i]
        
        # Modified order: Right, Center, Left
        crops = [
            ("Right", "in_w-out_w"),
            ("Center", "(in_w-out_w)/2"),
            ("Left", "0")
        ]

        for pos_label, offset in crops:
            if short_count >= len(master_metadata): break
            
            current_seo = master_metadata[short_count].copy()
            raw_title = current_seo.get("title", "Untitled")
            
            final_base_name = f"{sanitize_filename(raw_title)}_{pos_label}"
            video_output = OUTPUT_DIR / f"{final_base_name}.mp4"
            json_output = OUTPUT_DIR / f"{final_base_name}.json"
            
            current_audio_filter = AUDIO_FILTERS[short_count % 4]
            caption_text = raw_title.replace("'", "\\'").replace(":", "\\:")

            print(f"🎬 [{short_count+1}/12] Rendering: {final_base_name}")

            # FIXED: Removed 'stream_loop' from here. It is now in the command list.
            filter_complex = (
                f"[0:v:0]scale=-1:{t_h},crop={t_w}:{t_h}:{offset}:0,setsar=1,"
                f"drawtext=fontfile='{font_path}':text='{caption_text}':fontcolor=white:fontsize=50:"
                f"x=(w-text_w)/2:y=h*0.1:borderw=4:bordercolor=black[v_text];"
                
                f"[1:v]scale={t_w}:{t_h}[logo_scaled];"
                f"[v_text][logo_scaled]overlay=0:0[v_logo];"
                
                f"[2:v]scale={t_w}:{t_h}[sub_scaled];"
                f"[v_logo][sub_scaled]overlay=0:0:enable='between(t,15,20)'[v_final];"
                
                f"[3:a]{current_audio_filter},adelay=500|500[a_final]"
            )

            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1", "-i", str(video_path), # FIXED: Loop video here
                "-i", str(LOGO_CTA),
                "-i", str(SUB_CTA),
                "-stream_loop", "-1", "-i", str(audio_path), # Loop audio here
                "-filter_complex", filter_complex,
                "-map", "[v_final]", "-map", "[a_final]",
                "-t", "20",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "192k",
                str(video_output)
            ]

            try:
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
                with open(json_output, 'w', encoding='utf-8') as jf:
                    json.dump(current_seo, jf, indent=2)
                short_count += 1
            except subprocess.CalledProcessError as e:
                print(f"❌ Error on {final_base_name}: {e.stderr.decode()}")

    print(f"\n✨ DONE! 12 Shorts created in: {OUTPUT_DIR}")

if __name__ == "__main__":
    produce_synced_shorts()