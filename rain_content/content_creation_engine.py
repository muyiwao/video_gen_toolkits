import subprocess
import json
import math
import os
from pathlib import Path

# --- CORE UTILITY FUNCTIONS ---

def get_video_info(video_path):
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=duration,r_frame_rate",
        "-of", "json", str(video_path)
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    data = json.loads(result.stdout)
    fps_eval = data['streams'][0]['r_frame_rate'].split('/')
    fps = float(fps_eval[0]) / float(fps_eval[1])
    duration = float(data['streams'][0]['duration'])
    return duration, fps

def select_audio_file(audio_dir):
    audio_files = list(audio_dir.glob("*.mp3"))
    if not audio_files: return None
    print(f"\n🎵 Available Audio Tracks:")
    for i, file in enumerate(audio_files, 1):
        print(f"{i}. {file.name}")
    try:
        choice = int(input("\nSelect audio number: "))
        return audio_files[choice - 1]
    except: return None

def select_video_file(video_dir):
    video_files = list(video_dir.glob("*.mp4"))
    if not video_files: return None
    print(f"\n📺 Available Source Videos:")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file.name}")
    try:
        choice = int(input("\nSelect video number: "))
        return video_files[choice - 1]
    except: return None

# --- UPDATED AUDIO FILTER MAP ---
AUDIO_PROFILES = {
    "long": "bass=g=5:f=100,volume=-2dB",
    "short_r": "lowpass=f=1500,volume=-1dB", 
    "short_c": "highpass=f=1000,volume=0dB", 
    # Switched 'extraer' to 'extrastereo' (Standard wide-sound filter)
    "short_l": "aecho=0.8:0.3:40:0.3,extrastereo=m=2.5,volume=1dB", 
    "live": "compand,aecho=0.8:0.88:60:0.2"
}

# --- PROCESSING MODULES ---

def process_long_content():
    # 1. Paths Configuration
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    asset_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\long")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_long")
    audio_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\audio_pools")
    
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- ASSET PATHS ---
    img_logo_path = asset_dir / "screen-logo.png"
    
    # Selection helpers
    video_input = select_video_file(source_dir)
    audio_input = select_audio_file(audio_base_dir)
    if not video_input or not audio_input: return

    # 2. Resolution & Length Setup
    res_map = {
        "480p": "854:480", "720p": "1280:720", "1080p": "1920:1080", 
        "2k": "2560:1440", "4k": "3840:2160"
    }
    
    print(f"Available Resolutions: {', '.join(res_map.keys())}")
    res_choice = input("Enter resolution (e.g., 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1920:1080")

    try:
        # Note: Calculation reference from previous query (3min source = 1min yield)
        target_minutes = int(input("Enter total length in MINUTES (3min yield 1min): "))
        target_seconds = target_minutes * 60
    except ValueError: return

    # File Paths
    tile_file = output_dir / "temp_master_tile.mp4"
    segment_file = output_dir / "temp_1min_segment.mp4"
    temp_no_audio = output_dir / "temp_silent_final.mp4"
    list_file = output_dir / "concat_list.txt"
    final_output = output_dir / f"Final_Rain_{res_choice}_{target_minutes}min.mp4"

    # --- TEXT CONFIGURATION ---
    sub_text = "More rain content is on the way; subscribe so you never miss a moment of calm"
    text_color = "0x5cf629" # Hex converted for FFmpeg
    start_time = 5

    try:
        duration, fps = get_video_info(video_input)
        fade_dur = 1.0 if duration > 3 else 0.5
        loop_duration = duration - fade_dur

        # [STAGE 1] Seamless Tile
        print(f"\n[1/4] Creating Seamless Tile...")
        filter_tile = (
            f"[0:v]scale={target_res}:force_original_aspect_ratio=increase,crop={target_res},setsar=1,split[main][over];"
            f"[over]trim=start=0:end={fade_dur},setpts=PTS-STARTPTS[fadein];"
            f"[main]trim=start={fade_dur},setpts=PTS-STARTPTS[base];"
            f"[fadein]format=pix_fmts=yuva420p,fade=t=in:st=0:d={fade_dur}:alpha=1[alpha_fade];"
            f"[base][alpha_fade]overlay=x=0:y=0:shortest=1[v]"
        )
        subprocess.run(["ffmpeg", "-y", "-i", str(video_input), "-filter_complex", filter_tile, "-map", "[v]", "-c:v", "libx264", "-crf", "18", str(tile_file)], check=True)

        # [STAGE 2] 1-Minute Building Block
        tiles_needed = math.ceil(60 / loop_duration)
        with open(list_file, "w") as f:
            for _ in range(tiles_needed): f.write(f"file '{tile_file.name}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", "-t", "60", str(segment_file)], check=True)

        # [STAGE 3] Assembly with Logo and Subscription Text
        print(f"[3/4] Adding Visual Assets (Logo & Text)...")
        with open(list_file, "w") as f:
            for _ in range(target_minutes): f.write(f"file '{segment_file.name}'\n")

        filter_final = (
            f"[1:v]scale={target_res}[logo_sc];"
            f"[0:v][logo_sc]overlay=0:0:enable='gt(t,{start_time})'[v_logo];"
            f"[v_logo]drawtext=text='{sub_text}':font='Arial':fontsize=20:fontcolor={text_color}:"
            f"x=(w-text_w)/2:y=h-th-40:enable='gt(t,{start_time})':"
            f"shadowcolor=black@0.6:shadowx=2:shadowy=2[vout]"
        )

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-i", str(img_logo_path),
            "-filter_complex", filter_final,
            "-map", "[vout]", "-t", str(target_seconds),
            "-c:v", "libx264", "-crf", "21", "-preset", "veryfast", str(temp_no_audio)
        ], check=True)

        # [STAGE 4] Audio Mix (Applying "long" Audio Profile)
        print(f"[4/4] Adding Audio Loop with Filters...")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(temp_no_audio), 
            "-stream_loop", "-1", "-i", str(audio_input),
            "-map", "0:v", "-map", "1:a", 
            "-c:v", "copy", 
            "-af", AUDIO_PROFILES["long"], # <--- Applied Audio Filter Here
            "-c:a", "aac", "-b:a", "192k", "-shortest", 
            str(final_output)
        ], check=True)

        print(f"\n✅ SUCCESS! Output: {final_output}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        for temp in [tile_file, segment_file, list_file, temp_no_audio]:
            if temp.exists(): temp.unlink()

def process_shorts_batch():
    """
    Produces R, C, and L shorts. 
    Refactor: Dynamically scales attachments to match video resolution 
    while preserving original aspect ratio layout.
    """
    # --- 1. Path Configurations ---
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    audio_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\audio_pools")
    asset_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\shorts")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_shorts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Attachment Paths
    logo_cta = asset_dir / "logo-cta.png"
    sub_cta = asset_dir / "subscribe-cta.png"
    
    # --- 2. Runtime Selections ---
    video_input = select_video_file(source_dir)
    audio_input = select_audio_file(audio_base_dir)
    if not video_input or not audio_input: 
        print("Selection cancelled or files not found.")
        return

    # --- 3. Format & Resolution ---
    res_map = {"720p": "720:1280", "1080p": "1080:1920", "2k": "1440:2560", "4k": "2160:3840"}
    res_choice = input("\nEnter resolution (default 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1080:1920")
    t_w, t_h = map(int, target_res.split(':'))

    # --- 4. Configuration Mapping ---
    configs = {
        "R": {"profile": "short_r", "offset": "in_w-out_w"},
        "C": {"profile": "short_c", "offset": "(in_w-out_w)/2"},
        "L": {"profile": "short_l", "offset": "0"}
    }

    # --- 5. Batch Processing Loop ---
    for label, cfg in configs.items():
        print(f"\n--- Processing Variant: {label} ---")
        custom_name = input(f"📁 Enter filename for {label} version: ").strip()
        if not custom_name.lower().endswith(".mp4"):
            custom_name += ".mp4"
            
        caption = input(f"💬 Enter caption for {label} version: ").strip()
        final_output = output_dir / custom_name
        
        font_path = "C\\:/Windows/Fonts/arialbd.ttf"

        # Stage 1: Visual Filter Chain
        # Fix: We scale the inputs [1:v] and [2:v] to match target_res 
        # so they occupy the same relative space regardless of 720p/1080p/4k.
        filter_v = (
            # 1. Prepare Main Video
            f"[0:v]scale=-1:{t_h},crop={t_w}:{t_h}:{cfg['offset']}:0,setsar=1,"
            f"drawtext=fontfile='{font_path}':text='{caption}':fontcolor=white:fontsize=90:"
            f"x=(w-text_w)/2:y=h*0.1:borderw=4:bordercolor=black[v_text];"
            
            # 2. Scale Logo to fit video resolution and overlay
            f"[1:v]scale={t_w}:{t_h}[logo_scaled];"
            f"[v_text][logo_scaled]overlay=0:0[v_logo];"
            
            # 3. Scale Subscribe CTA to fit video resolution and overlay (timed)
            f"[2:v]scale={t_w}:{t_h}[sub_scaled];"
            f"[v_logo][sub_scaled]overlay=0:0:enable='between(t,15,20)'[v]"
        )

        try:
            print(f"🎬 Rendering {custom_name} with original-scale attachments...")
            subprocess.run([
                "ffmpeg", "-y", 
                "-stream_loop", "-1", "-i", str(video_input), # Input 0
                "-i", str(logo_cta),                           # Input 1
                "-i", str(sub_cta),                            # Input 2
                "-stream_loop", "-1", "-i", str(audio_input), # Input 3
                "-filter_complex", filter_v, 
                "-af", AUDIO_PROFILES[cfg['profile']],
                "-map", "[v]", 
                "-map", "3:a", 
                "-t", "20", 
                "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "192k", 
                str(final_output)
            ], check=True)
            print(f"✅ Success: {final_output.name}")

        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg failed on variant {label}. Check paths or assets.")
            continue

    print(f"\n✨ Batch complete. Files saved to: {output_dir}")

def process_live_content():
    """
    Optimized Live Content Generator:
    1. Fixes missing logo by using -loop 1 on image inputs.
    2. Explicitly scales logos within the filter chain to match target res.
    3. Maintains 2-stage assembly for speed.
    """
    # 1. Path Configurations
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    audio_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\audio_pools")
    live_asset_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\live")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_live")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Source Selection
    video_input = select_video_file(source_dir)
    audio_input = select_audio_file(audio_base_dir)
    if not video_input or not audio_input: return

    # 3. Format Configuration
    custom_name = input("\n📁 Output filename: ").strip()
    if not custom_name.endswith(".mp4"): custom_name += ".mp4"

    print("\n📐 Select Aspect Ratio:")
    print("1. Horizontal (16:9)")
    print("2. Vertical (9:16)")
    ar_choice = input("Selection (1-2): ").strip()
    res_choice = input("Enter resolution (e.g., 1080p): ").lower().strip()
    
    target_minutes = int(input("Enter final length in MINUTES (1min yield 1min): "))
    target_seconds = target_minutes * 60

    # Resolution Maps
    h_res = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080", "2k": "2560:1440", "4k": "3840:2160"}
    v_res = {"480p": "480:854", "720p": "720:1280", "1080p": "1080:1920", "2k": "1440:2560", "4k": "2160:3840"}

    # 4. Filter Configuration with Explicit Scaling
    if ar_choice == '2':
        res = v_res.get(res_choice, "1080:1920")
        t_w, t_h = res.split(':')
        logo_path = live_asset_dir / "screen-logo_9_16.png"
        # Scale video to vertical, then overlay scaled logo
        filter_complex = (
            f"[0:v]scale=-1:{t_h},crop={t_w}:{t_h}:(in_w-out_w)/2:0,setsar=1[bg];"
            f"[1:v]scale={t_w}:{t_h}[l_scaled];"
            f"[bg][l_scaled]overlay=0:0:enable='gt(t,5)'[v]"
        )
    else:
        res = h_res.get(res_choice, "1920:1080")
        t_w, t_h = res.split(':')
        logo_path = live_asset_dir / "screen-logo_16_9.png"
        # Scale video to horizontal, then overlay scaled logo
        filter_complex = (
            f"[0:v]scale={res}:force_original_aspect_ratio=increase,crop={res},setsar=1[bg];"
            f"[1:v]scale={t_w}:{t_h}[l_scaled];"
            f"[bg][l_scaled]overlay=0:0:enable='gt(t,5)'[v]"
        )

    # Temporary files
    tile_file = output_dir / "temp_live_tile.mp4"
    list_file = output_dir / "live_concat_list.txt"
    final_output = output_dir / custom_name

    try:
        # --- STAGE 1: Create Master Tile ---
        print(f"\n[1/2] Encoding 1-minute master tile with logo...")
        subprocess.run([
            "ffmpeg", "-y", 
            "-stream_loop", "-1", "-i", str(video_input), 
            "-loop", "1", "-i", str(logo_path),  # FIX: -loop 1 makes the image persistent
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-t", "60", # The master tile is 1 minute
            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-an", 
            str(tile_file)
        ], check=True)

        # --- STAGE 2: Final Assembly ---
        print(f"[2/2] Assembling {target_minutes}m video (Stream Copying)...")
        
        with open(list_file, "w") as f:
            for _ in range(target_minutes):
                f.write(f"file '{tile_file.name}'\n")

        subprocess.run([
            "ffmpeg", "-y", 
            "-f", "concat", "-safe", "0", "-i", str(list_file), 
            "-stream_loop", "-1", "-i", str(audio_input),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", 
            "-af", AUDIO_PROFILES["live"], 
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(target_seconds),
            "-shortest", str(final_output)
        ], check=True)

        print(f"\n✅ Done! File saved: {final_output}")

    finally:
        if tile_file.exists(): tile_file.unlink()
        if list_file.exists(): list_file.unlink()

if __name__ == "__main__":
    print("--- CONTENT GENERATION TOOLKIT (FFMPEG NATIVE AUDIO) ---")
    print("1. Long | 2. Shorts Batch | 3. Live")
    choice = input("\nChoice: ").strip()
    if choice == '1': process_long_content()
    elif choice == '2': process_shorts_batch()
    elif choice == '3': process_live_content()