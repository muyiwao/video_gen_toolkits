import subprocess
import json
import math
import os
from pathlib import Path
import sys

# Adds the project root to the python path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from rain_content.scripts import thumbnail_extractor

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

def select_optional_file(directory, label):
    """Helper to let user pick a file or skip it."""
    files = list(directory.glob("*.mp3")) + list(directory.glob("*.wav"))
    if not files:
        print(f"No files found in {directory}. Skipping {label}.")
        return None
    
    print(f"\n--- {label} Selection ---")
    print("0: Skip this sound")
    for i, f in enumerate(files, 1):
        print(f"{i}: {f.name}")
    
    choice = input(f"Select {label} (0-{len(files)}): ").strip()
    if choice == "0" or not choice:
        return None
    try:
        return files[int(choice) - 1]
    except (ValueError, IndexError):
        return None

def process_long_content():
    # 1. Paths Configuration
    base_path = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
    source_dir = base_path / "rain_content" / "recorded" / "enhanced"
    asset_dir = base_path / "rain_content" / "attachments" / "long"
    output_dir = base_path / "output" / "output_long"
    sfx_pool = base_path / "input" / "audio_pools" / "sfx"
    music_pool = base_path / "input" / "audio_pools" / "music"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    img_logo_path = asset_dir / "screen-logo.png"
    
    # 2. SELECTION
    video_input = select_video_file(source_dir) 
    rain_input = select_audio_file(base_path / "input" / "audio_pools" / "rain") 
    
    if not video_input or not rain_input: return

    sfx_input = select_optional_file(sfx_pool, "Secondary SFX")
    music_input = select_optional_file(music_pool, "Tertiary Music")

    # --- RAIN INTENSITY / SPEED SECTION ---
    print("\n--- Rain Speed Adjustment ---")
    try:
        speed_input = input("Enter Speed Factor [Default 1.0]: ").strip()
        speed_factor = float(speed_input) if speed_input else 1.0
    except ValueError:
        speed_factor = 1.0

    # --- VOLUME ALLOCATION SECTION ---
    print("\n--- Volume Allocation ---")
    try:
        rain_vol = float(input("Rain Volume % [Default 75]: ") or 75) / 100
        sfx_vol = float(input("SFX Volume % [Default 15]: ") or 15) / 100 if sfx_input else 0.15
        music_vol = float(input("Music Volume % [Default 10]: ") or 10) / 100 if music_input else 0.10
    except ValueError:
        rain_vol, sfx_vol, music_vol = 0.75, 0.15, 0.10

    # 3. Resolution
    res_map = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080"}
    res_choice = input("\nEnter resolution (e.g., 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1920:1080")

    # --- DURATION PREDICTION & APPROVAL LOOP ---
    duration, _ = get_video_info(video_input)
    adj_duration = duration * speed_factor
    fade_dur = 1.0
    loop_duration = adj_duration - fade_dur # The actual 'usable' time per loop

    while True:
        try:
            print(f"\n--- Duration Prediction ---")
            print(f"One loop yields approx. {loop_duration / 60:.2f} minutes of seamless footage.")
            target_minutes = float(input("Enter DESIRED final length in MINUTES (1.5min yield 1min): "))
            
            # Prediction Logic
            # We calculate how many segments it takes to reach that time
            total_required_seconds = target_minutes * 60
            num_loops_needed = math.ceil(total_required_seconds / loop_duration)
            predicted_raw_input_needed = (num_loops_needed * duration) / 60
            
            print(f"\n📝 PREDICTION REPORT:")
            print(f"Target Output: {target_minutes:.2f} minutes")
            print(f"Loops Required: {num_loops_needed}")
            print(f"Estimated Input Needed: {predicted_raw_input_needed:.2f} minutes of recorded footage")
            print(f"Final File Size Estimate: ~{(target_minutes * 15):.0f} MB (at 1080p)")
            
            confirm = input("\nAccept these parameters and start processing? (y/n): ").lower().strip()
            if confirm == 'y':
                target_seconds = target_minutes * 60
                break
            else:
                print("Adjustment requested. Please enter a new duration.")
        except ValueError:
            print("❌ Invalid number. Please enter a decimal or integer for minutes.")

    # File Paths
    tile_file = output_dir / "temp_master_tile.mp4"
    segment_file = output_dir / "temp_1min_segment.mp4"
    temp_no_audio = output_dir / "temp_silent_final.mp4"
    list_file = output_dir / "concat_list.txt"
    final_output = output_dir / f"Final_Rain_Mixed_{target_minutes}min.mp4"

    sub_text = "More rain content is on the way; subscribe so you never miss a moment of calm"
    text_color = "0x5cf629" 

    try:
        # --- STAGE 1: PREPARE BASE LOOP ---
        print(f"\n[1/4] Preparing Video Loop...")
        filter_tile = (
            f"[0:v]setpts={speed_factor}*PTS,"
            f"scale={target_res}:force_original_aspect_ratio=increase,crop={target_res},setsar=1,split[main][over];"
            f"[over]trim=start=0:end={fade_dur},setpts=PTS-STARTPTS[fadein];"
            f"[main]trim=start={fade_dur},setpts=PTS-STARTPTS[base];"
            f"[fadein]format=pix_fmts=yuva420p,fade=t=in:st=0:d={fade_dur}:alpha=1[alpha_fade];"
            f"[base][alpha_fade]overlay=x=0:y=0:shortest=1[v]"
        )
        subprocess.run(["ffmpeg", "-y", "-i", str(video_input), "-filter_complex", filter_tile, "-map", "[v]", "-c:v", "libx264", "-crf", "18", str(tile_file)], check=True)

        # Build 1-minute segment as a standard block
        tiles_in_one_min = math.ceil(60 / loop_duration)
        with open(list_file, "w") as f:
            for _ in range(tiles_in_one_min): f.write(f"file '{tile_file.name}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", "-t", "60", str(segment_file)], check=True)

        # --- STAGE 2: ASSEMBLE MASTER ---
        print(f"[2/4] Assembling {target_minutes} Minute Silent Master...")
        minutes_to_concat = math.ceil(target_minutes)
        with open(list_file, "w") as f:
            for _ in range(minutes_to_concat): f.write(f"file '{segment_file.name}'\n")

        scroll_speed = 60
        filter_final = (
            f"[1:v]scale={target_res}[logo_sc];"
            f"[0:v][logo_sc]overlay=0:0:enable='gt(t,5)'[v_logo];"
            f"[v_logo]drawtext=text='{sub_text}':font='Arial':fontsize=22:fontcolor={text_color}:"
            f"x='mod(t*{scroll_speed}, w+text_w)-text_w':y=h-th-60:enable='gt(t,5)':"
            f"box=1:boxcolor=black@0.4:boxborderw=12:"
            f"shadowcolor=black@0.8:shadowx=2:shadowy=2[vout]"
        )

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-i", str(img_logo_path),
            "-filter_complex", filter_final,
            "-map", "[vout]", "-t", str(target_seconds),
            "-c:v", "libx264", "-crf", "21", "-preset", "veryfast", str(temp_no_audio)
        ], check=True)

        # --- STAGE 4: AUDIO MIX ---
        print(f"\n[4/4] Blending Audio Tracks...")
        audio_inputs = ["-stream_loop", "-1", "-i", str(rain_input)]
        filter_audio = f"[1:a]volume={rain_vol}[rain];"
        mix_labels = "[rain]"
        mix_count = 1

        if sfx_input:
            audio_inputs += ["-stream_loop", "-1", "-i", str(sfx_input)]
            filter_audio += f"[{mix_count + 1}:a]volume={sfx_vol}[sfx];"
            mix_labels += "[sfx]"
            mix_count += 1

        if music_input:
            audio_inputs += ["-stream_loop", "-1", "-i", str(music_input)]
            filter_audio += f"[{mix_count + 1}:a]volume={music_vol}[music];"
            mix_labels += "[music]"
            mix_count += 1

        filter_audio += f"{mix_labels}amix=inputs={mix_count}:duration=first:dropout_transition=0:normalize=0[a_mixed]"

        cmd = [
            "ffmpeg", "-y", "-i", str(temp_no_audio)
        ] + audio_inputs + [
            "-filter_complex", filter_audio,
            "-map", "0:v", "-map", "[a_mixed]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
            "-shortest", str(final_output)
        ]

        subprocess.run(cmd, check=True)
        print(f"\n✅ SUCCESS! {target_minutes}min video created.")

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
    if choice == '1':
        process_long_content()
        
        # --- NEW THUMBNAIL PROMPT ---
        make_thumb = input("\n🖼️  Generate thumbnail for this long video? (y/n): ").strip().lower()
        if make_thumb == 'y':
            thumbnail_extractor.generate_universal_thumbs()
        else:
            print("⏭️  Skipping thumbnail generation.")
            
    elif choice == '2': 
        process_shorts_batch()
    elif choice == '3': 
        process_live_content()