import subprocess
import os

# --- DIRECTORY CONFIGURATION ---
ASSET_DIR = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\attachments\shorts"
MAIN_V_DIR = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\raw_lessons"
OUTPUT_DIR = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\output"

PATHS = {
    "v1":     os.path.join(ASSET_DIR, "intro_video.mp4"),
    "v2":     os.path.join(ASSET_DIR, "subscribe-cta.mp4"),
    "v3":     os.path.join(ASSET_DIR, "outtro_video.mp4"),
    "img1":   os.path.join(ASSET_DIR, "background_with_logo.png"),
    "img2":   os.path.join(ASSET_DIR, "related_video_pointer.png"),
}

def parse_range(range_str):
    result = set()
    for part in range_str.split(','):
        part = part.strip()
        if not part: continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                result.update(range(start, end + 1))
            except: continue
        else:
            try: result.add(int(part))
            except: continue
    return sorted(list(result))

def get_audio_speed_filters(speed):
    filters = []
    curr_speed = speed
    while curr_speed > 2.0:
        filters.append("atempo=2.0")
        curr_speed /= 2.0
    while curr_speed < 0.5:
        filters.append("atempo=0.5")
        curr_speed /= 0.5
    filters.append(f"atempo={curr_speed:.2f}")
    return ",".join(filters)

def build_ffmpeg_command(main_v_path, output_path, caption_text, text_scale=100, speed=1.0):
    W, H = 1080, 1920
    target_width = int(W * (text_scale / 100))
    video_pts = 1.0 / speed
    audio_speed_chain = get_audio_speed_filters(speed)

    # CAPTION STYLING
    # font='Open Sans': ensure this is installed on your OS.
    # enable='lt(t,15)': Caption disappears after 15 seconds.
    drawtext_filter = (
        f"drawtext=text='{caption_text}':font='Open Sans':fontcolor=white:fontsize=75:"
        f"box=1:boxcolor=red@1.0:boxborderw=25:"
        f"x=(w-text_w)/2:y=250:enable='lt(t,15)'" 
    )

    filter_complex = (
        f"[4:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[bg];"
        f"[0:v]scale={target_width}:-1,setpts={video_pts:.4f}*PTS,colorkey=0x000000:0.1:0.1[main_v_key];"
        f"[0:a]{audio_speed_chain}[main_a_speed];" 
        f"[bg][main_v_key]overlay=x=(W-w)/2:y=(H-h)/2[base];"
        
        f"[base]{drawtext_filter}[with_caption];"
        
        f"[2:v]scale={W}:-1[cta_v];"
        f"[with_caption][cta_v]overlay=0:(H-h)/2:enable='lt(mod(t,30),3)'[with_cta];"
        f"[5:v]scale=1000:-1[ptr];"
        f"[with_cta][ptr]overlay=x=(W-w)/2:y=H-h:enable='gt(t,10)'[lesson_final_v];"
        
        f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[v1_f];"
        f"[3:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[v3_f];"
        
        f"[v1_f][1:a][lesson_final_v][main_a_speed][v3_f][3:a]concat=n=3:v=1:a=1[v_out][a_out]"
    )

    return [
        'ffmpeg', '-y',
        '-i', main_v_path,
        '-i', PATHS["v1"],
        '-i', PATHS["v2"],
        '-i', PATHS["v3"],
        '-i', PATHS["img1"],
        '-i', PATHS["img2"],
        '-filter_complex', filter_complex,
        '-map', '[v_out]', '-map', '[a_out]',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '192k',
        output_path
    ]

if __name__ == "__main__":
    # --- GLOBAL PARAMETERS (Set once for the whole batch) ---
    try:
        range_input = input("Enter video numbers/ranges (e.g., 1-10): ")
        target_indices = parse_range(range_input)
        
        u_caption = input("Enter the GLOBAL caption for this batch: ")
        
        u_scale = float(input("Main Text Scale (1-500, default 100): ") or 100)
        u_speed = float(input("Video Speed (0.1-30.0, default 1.0): ") or 1.0)
    except Exception as e:
        print(f"❌ Input error: {e}")
        exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- BATCH PROCESSING LOOP ---
    for idx in target_indices:
        main_filename = f"{idx}.mp4"
        in_p = os.path.join(MAIN_V_DIR, main_filename)
        out_p = os.path.join(OUTPUT_DIR, main_filename)

        if os.path.exists(in_p):
            print(f"\n🎬 Processing {main_filename} with caption: '{u_caption}'...")
            try:
                subprocess.run(build_ffmpeg_command(in_p, out_p, u_caption, u_scale, u_speed), check=True)
                print(f"✅ Success: {main_filename}")
            except subprocess.CalledProcessError as e:
                print(f"❌ FFmpeg Error on {main_filename}")
        else:
            print(f"⚠️ Skipping {main_filename}: File not found in {MAIN_V_DIR}")

    print("\n✨ All videos in this batch are complete!")