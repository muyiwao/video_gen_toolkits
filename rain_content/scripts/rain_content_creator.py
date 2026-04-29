import subprocess
import json
import math
import os
from pathlib import Path
import sys
import re

# Adds the project root to the python path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from scripts import thumbnail_extractor

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
def format_duration(total_minutes):
    """Converts decimal minutes into a formatted string (Hours, Minutes, Seconds)."""
    total_seconds = int(total_minutes * 60)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    if seconds > 0: parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0s"

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

def format_duration(total_minutes):
    """Converts decimal minutes into a formatted string (Hours, Minutes, Seconds)."""
    total_seconds = int(total_minutes * 60)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    if seconds > 0: parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0s"

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

    # --- Runtime Inputs ---
    print("\n--- Social CTA Ticker ---")
    default_sub = "More rain content is on the way; Subscribe so you never miss a moment of calm"
    sub_text = input(f"Enter Ticker Text [Leave blank for default]: ").strip() or default_sub

    print("\n--- Speed & Volume Settings ---")
    try:
        speed_input = input("Enter Speed Factor [Default 1.0]: ").strip()
        speed_factor = float(speed_input) if speed_input else 1.0
        
        # --- NEW: Master Volume Adjustment ---
        print("\n[Master Audio Gain]")
        master_vol_pct = float(input("Final Output Volume % (e.g., 50 for half, 150 for louder) [Default 100]: ") or 100)
        master_gain = master_vol_pct / 100

        print("\n[Layer Balancing]")
        rain_vol = float(input("Rain Layer Volume % [Default 75]: ") or 75) / 100
        sfx_vol = float(input("SFX Layer Volume % [Default 15]: ") or 15) / 100 if sfx_input else 0.15
        music_vol = float(input("Music Layer Volume % [Default 10]: ") or 10) / 100 if music_input else 0.10
    except ValueError:
        speed_factor, master_gain, rain_vol, sfx_vol, music_vol = 1.0, 1.0, 0.75, 0.15, 0.10

    # 3. Resolution
    res_map = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080", "2k": "2560:1440", "4k": "3840:2160"}
    res_choice = input("\nEnter resolution (e.g., 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1920:1080")

    # --- DURATION PREDICTION ---
    duration, _ = get_video_info(video_input)
    adj_duration = duration * speed_factor
    fade_dur = 1.0
    loop_duration = adj_duration - fade_dur 

    while True:
        try:
            print(f"\n--- Duration Setup ---")
            target_minutes = float(input("Enter DESIRED final length in DECIMAL MINUTES: "))
            target_seconds = int(target_minutes * 60)
            formatted_time = format_duration(target_minutes)
            break
        except ValueError:
            print("❌ Invalid number.")

    tile_file = output_dir / "temp_master_tile.mp4"
    segment_file = output_dir / "temp_1min_segment.mp4"
    temp_no_audio = output_dir / "temp_silent_final.mp4"
    list_file = output_dir / "concat_list.txt"
    final_output = output_dir / f"Rain_Video_{formatted_time.replace(' ', '_')}.mp4"

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

        tiles_in_one_min = math.ceil(60 / loop_duration)
        with open(list_file, "w") as f:
            for _ in range(tiles_in_one_min): f.write(f"file '{tile_file.name}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", "-t", "60", str(segment_file)], check=True)

        # --- STAGE 2: ASSEMBLE MASTER WITH FULL-WIDTH TICKER ---
        print(f"[2/4] Assembling {formatted_time} Silent Master...")
        minutes_to_concat = math.ceil(target_minutes)
        with open(list_file, "w") as f:
            for _ in range(minutes_to_concat): f.write(f"file '{segment_file.name}'\n")

        scroll_speed = 100
        filter_final = (
            f"[1:v]scale={target_res}[logo_sc];"
            f"[0:v][logo_sc]overlay=0:0:enable='gt(t,5)'[v_logo];"
            f"[v_logo]drawbox=y=ih-80:color=black@0.6:width=iw:height=60:t=fill:enable='gt(t,5)'[v_bg];"
            f"[v_bg]drawtext=text='{sub_text}':font='Arial':fontsize=24:fontcolor=0x5cf629:"
            f"x='mod(t*{scroll_speed}, w+text_w)-text_w':y=h-62:enable='gt(t,5)':"            
            f"shadowcolor=black@0.8:shadowx=2:shadowy=2[vout]"
        )

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-i", str(img_logo_path),
            "-filter_complex", filter_final,
            "-map", "[vout]", "-t", str(target_seconds),
            "-c:v", "libx264", "-crf", "21", "-preset", "veryfast", str(temp_no_audio)
        ], check=True)

        # --- STAGE 3: AUDIO MIX WITH MASTER GAIN ---
        print(f"\n[3/4] Blending Audio Tracks with Master Gain...")
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

        # Apply amix, then apply the master_gain to the result
        filter_audio += (
            f"{mix_labels}amix=inputs={mix_count}:duration=first:dropout_transition=0:normalize=0[a_mixed];"
            f"[a_mixed]volume={master_gain}[final_a]"
        )

        subprocess.run([
            "ffmpeg", "-y", "-i", str(temp_no_audio)
        ] + audio_inputs + [
            "-filter_complex", filter_audio,
            "-map", "0:v", "-map", "[final_a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
            "-shortest", str(final_output)
        ], check=True)

        print(f"\n✅ SUCCESS! {formatted_time} video created with {master_vol_pct}% volume.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        for temp in [tile_file, segment_file, list_file, temp_no_audio]:
            if temp.exists(): temp.unlink()

def sanitize_filename(name):
    """Removes illegal characters and replaces spaces with underscores."""
    return re.sub(r'[\\/*?:"<>|]', '', name).replace(' ', '_')

def process_shorts_batch():
    """
    Produces R, C, and L shorts with composite audio (Rain + Brown Noise + SFX/Music)
    and Matching-Pair JSON metadata files.
    """
    # --- 1. Path Configurations ---
    base_path = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
    source_dir = base_path / "rain_content" / "recorded" / "enhanced"
    audio_base_dir = base_path / "input" / "audio_pools"
    asset_dir = base_path / "rain_content" / "attachments" / "shorts"
    output_dir = base_path / "output" / "output_shorts"
    json_metadata_path = base_path / "input" / "metadata.json"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # --- 2. Load Master Metadata ---
    if not json_metadata_path.exists():
        print(f"❌ Error: Master metadata not found at {json_metadata_path}")
        return
    
    with open(json_metadata_path, 'r', encoding='utf-8') as f:
        master_metadata = json.load(f)
    
    # --- 3. Runtime Selections ---
    video_input = select_video_file(source_dir)
    rain_input = select_audio_file(audio_base_dir / "rain") 
    
    if not video_input or not rain_input: return

    sfx_input = select_optional_file(audio_base_dir / "sfx", "Secondary SFX")
    music_input = select_optional_file(audio_base_dir / "music", "Tertiary Music")

    # --- 4. Duration & Resolution ---
    dur_raw = input("\nTarget Duration (e.g., 59 or 0.5m) [Default 59s]: ").strip().lower()
    target_seconds = float(dur_raw.replace('m', '')) * 60 if 'm' in dur_raw else float(dur_raw or 59)

    res_map = {"720p": "720:1280", "1080p": "1080:1920", "2k": "1440:2560", "4k": "2160:3840"}
    res_choice = input("Enter resolution (default 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1080:1920")
    t_w, t_h = map(int, target_res.split(':'))

    # --- 5. Volume Allocation ---
    try:
        rain_vol = float(input("\nRain Volume % [Default 75]: ") or 75) / 100
        # Brown Noise set to a subtle 5% for low-end "rumble" support
        brown_vol = 0.05 
        sfx_vol = float(input("SFX Volume % [Default 15]: ") or 15) / 100 if sfx_input else 0.15
        music_vol = float(input("Music Volume % [Default 10]: ") or 10) / 100 if music_input else 0.10
    except ValueError:
        rain_vol, brown_vol, sfx_vol, music_vol = 0.75, 0.05, 0.15, 0.10

    configs = {
        "Right": {"profile": "short_r", "offset": "in_w-out_w"},
        "Center": {"profile": "short_c", "offset": "(in_w-out_w)/2"},
        "Left": {"profile": "short_l", "offset": "0"}
    }

    # --- 6. Batch Processing Loop ---
    short_index = 0
    for label, cfg in configs.items():
        if short_index >= len(master_metadata):
            break

        current_seo = master_metadata[short_index]
        raw_title = current_seo.get("title", "Untitled_Short")
        base_name = f"{sanitize_filename(raw_title)}_{label}"
        video_output = output_dir / f"{base_name}.mp4"
        json_output = output_dir / f"{base_name}.json"

        print(f"\n🎬 Rendering Pair: {base_name}")
        
        sub_start, sub_end = max(0, target_seconds - 10), target_seconds
        font_path = "C\\:/Windows/Fonts/arialbd.ttf"
        caption = raw_title.replace("'", "\\'").replace(":", "\\:")

        # --- Visual Filter ---
        filter_v = (
            f"[0:v]scale=-1:{t_h},crop={t_w}:{t_h}:{cfg['offset']}:0,setsar=1,"
            f"drawtext=fontfile='{font_path}':text='{caption}':fontcolor=white:fontsize=90:"
            f"x=(w-text_w)/2:y=h*0.1:borderw=4:bordercolor=black[v_text];"
            f"[1:v]scale={t_w}:{t_h}[logo_scaled];"
            f"[v_text][logo_scaled]overlay=0:0[v_logo];"
            f"[2:v]scale={t_w}:{t_h}[sub_scaled];"
            f"[v_logo][sub_scaled]overlay=0:0:enable='between(t,{sub_start},{sub_end})'[v]"
        )

        # --- Audio Filter (Brown Noise Integrated) ---
        audio_inputs = ["-stream_loop", "-1", "-i", str(rain_input)]
        
        # 1. Generate brown noise and set volumes for Rain + Brown
        filter_a = (
            f"anoisesrc=d={target_seconds}:c=brown:r=44100[brn_raw];"
            f"[brn_raw]volume={brown_vol}[brn];"
            f"[3:a]volume={rain_vol}[rain];"
        )
        mix_labels = "[rain][brn]"
        mix_count = 2 # Starting count is 2 (Rain + Brown Noise)

        if sfx_input:
            audio_inputs += ["-stream_loop", "-1", "-i", str(sfx_input)]
            filter_a += f"[{3 + (mix_count-1)}:a]volume={sfx_vol}[sfx];"
            mix_labels += "[sfx]"
            mix_count += 1
        
        if music_input:
            audio_inputs += ["-stream_loop", "-1", "-i", str(music_input)]
            filter_a += f"[{3 + (mix_count-1)}:a]volume={music_vol}[music];"
            mix_labels += "[music]"
            mix_count += 1

        filter_a += f"{mix_labels}amix=inputs={mix_count}:duration=first[a_mixed];"
        filter_a += f"[a_mixed]{AUDIO_PROFILES[cfg['profile']]}[final_a]"

        try:
            subprocess.run([
                "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(video_input),
                "-i", str(base_path / "rain_content/attachments/shorts/logo-cta.png"),
                "-i", str(base_path / "rain_content/attachments/shorts/subscribe-cta.png")
            ] + audio_inputs + [
                "-filter_complex", f"{filter_v};{filter_a}",
                "-map", "[v]", "-map", "[final_a]",
                "-t", str(target_seconds),
                "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "192k", str(video_output)
            ], check=True)

            with open(json_output, 'w', encoding='utf-8') as jf:
                json.dump(current_seo, jf, indent=2)
            
            print(f"✅ Created: {video_output.name}")
            short_index += 1

        except subprocess.CalledProcessError:
            print(f"❌ FFmpeg failed on {label} variant.")
            continue

    print(f"\n✨ Batch complete. All pairs saved to: {output_dir}")

def process_live_content():
    """
    Optimized Live Content Generator with Multi-Track Audio Mixing.
    Blends Rain, SFX, and Music paths with percentage-based volume control.
    """
    # 1. Path Configurations
    base_path = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
    source_dir = base_path / "rain_content" / "recorded" / "enhanced"
    audio_base_dir = base_path / "input" / "audio_pools"
    live_asset_dir = base_path / "rain_content" / "attachments" / "live"
    output_dir = base_path / "output" / "output_live"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Source Selection (Video + Audio Tracks)
    video_input = select_video_file(source_dir)
    rain_input = select_audio_file(audio_base_dir / "rain") # Primary Track
    
    if not video_input or not rain_input: 
        print("Essential video or rain audio missing.")
        return

    # Optional Tracks
    sfx_input = select_optional_file(audio_base_dir / "sfx", "Secondary SFX")
    music_input = select_optional_file(audio_base_dir / "music", "Tertiary Music")

    # 3. Format & Timing Configuration
    custom_name = input("\n📁 Output filename: ").strip()
    if not custom_name.endswith(".mp4"): custom_name += ".mp4"

    print("\n📐 Select Aspect Ratio:")
    print("1. Horizontal (16:9)")
    print("2. Vertical (9:16)")
    ar_choice = input("Selection (1-2): ").strip()
    res_choice = input("Enter resolution (e.g., 1080p): ").lower().strip()
    
    target_minutes = int(input("Enter final length in MINUTES (1min yield 1min): "))
    target_seconds = target_minutes * 60

    # 4. Volume Allocation Section
    print("\n--- Volume Allocation ---")
    try:
        rain_vol = float(input("Rain Volume % [Default 75]: ") or 75) / 100
        sfx_vol = float(input("SFX Volume % [Default 15]: ") or 15) / 100 if sfx_input else 0.0
        music_vol = float(input("Music Volume % [Default 10]: ") or 10) / 100 if music_input else 0.0
    except ValueError:
        rain_vol, sfx_vol, music_vol = 0.75, 0.15, 0.10

    # Resolution Maps
    h_res = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080", "2k": "2560:1440", "4k": "3840:2160"}
    v_res = {"480p": "480:854", "720p": "720:1280", "1080p": "1080:1920", "2k": "1440:2560", "4k": "2160:3840"}

    # 5. Visual Filter Configuration
    if ar_choice == '2':
        res = v_res.get(res_choice, "1080:1920")
        t_w, t_h = res.split(':')
        logo_path = live_asset_dir / "screen-logo_9_16.png"
        filter_v = (
            f"[0:v]scale=-1:{t_h},crop={t_w}:{t_h}:(in_w-out_w)/2:0,setsar=1[bg];"
            f"[1:v]scale={t_w}:{t_h}[l_scaled];"
            f"[bg][l_scaled]overlay=0:0:enable='gt(t,5)'[v]"
        )
    else:
        res = h_res.get(res_choice, "1920:1080")
        t_w, t_h = res.split(':')
        logo_path = live_asset_dir / "screen-logo_16_9.png"
        filter_v = (
            f"[0:v]scale={res}:force_original_aspect_ratio=increase,crop={res},setsar=1[bg];"
            f"[1:v]scale={t_w}:{t_h}[l_scaled];"
            f"[bg][l_scaled]overlay=0:0:enable='gt(t,5)'[v]"
        )

    # 6. Audio Mixing Configuration (Applied in Stage 2)
    # Start inputs for audio at index 1 in the second subprocess call
    audio_inputs_cmd = ["-stream_loop", "-1", "-i", str(rain_input)]
    filter_a = f"[1:a]volume={rain_vol}[rain];"
    mix_labels = "[rain]"
    mix_count = 1

    if sfx_input:
        audio_inputs_cmd += ["-stream_loop", "-1", "-i", str(sfx_input)]
        filter_a += f"[{1 + mix_count}:a]volume={sfx_vol}[sfx];"
        mix_labels += "[sfx]"
        mix_count += 1
    
    if music_input:
        audio_inputs_cmd += ["-stream_loop", "-1", "-i", str(music_input)]
        filter_a += f"[{1 + mix_count}:a]volume={music_vol}[music];"
        mix_labels += "[music]"
        mix_count += 1

    filter_a += f"{mix_labels}amix=inputs={mix_count}:duration=first:dropout_transition=0[a_mixed];"
    filter_a += f"[a_mixed]{AUDIO_PROFILES['live']}[final_a]"

    # Temporary files
    tile_file = output_dir / "temp_live_tile.mp4"
    list_file = output_dir / "live_concat_list.txt"
    final_output = output_dir / custom_name

    try:
        # --- STAGE 1: Create Master Visual Tile (No Audio) ---
        print(f"\n[1/2] Encoding 1-minute visual master tile...")
        subprocess.run([
            "ffmpeg", "-y", 
            "-stream_loop", "-1", "-i", str(video_input), 
            "-loop", "1", "-i", str(logo_path),
            "-filter_complex", filter_v,
            "-map", "[v]",
            "-t", "60",
            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-an", 
            str(tile_file)
        ], check=True)

        # --- STAGE 2: Final Assembly & Audio Mixing ---
        print(f"[2/2] Mixing audio and assembling {target_minutes}m video...")
        
        with open(list_file, "w") as f:
            for _ in range(target_minutes):
                f.write(f"file '{tile_file.name}'\n")

        subprocess.run([
            "ffmpeg", "-y", 
            "-f", "concat", "-safe", "0", "-i", str(list_file)
        ] + audio_inputs_cmd + [
            "-filter_complex", filter_a,
            "-map", "0:v", "-map", "[final_a]",
            "-c:v", "copy", 
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(target_seconds),
            str(final_output)
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
            thumbnail_extractor.generate_4k_rain_thumbs()
        else:
            print("⏭️  Skipping thumbnail generation.")
            
    elif choice == '2': 
        process_shorts_batch()
    elif choice == '3': 
        process_live_content()