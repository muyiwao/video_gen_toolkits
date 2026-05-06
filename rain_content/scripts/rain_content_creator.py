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

# --- UPDATED AUDIO FILTER MAP ---
AUDIO_PROFILES = {
    "long": "bass=g=5:f=100,volume=-2dB",
    "short_r": "lowpass=f=1500,volume=-1dB", 
    "short_c": "highpass=f=1000,volume=0dB", 
    # Switched 'extraer' to 'extrastereo' (Standard wide-sound filter)
    "short_l": "aecho=0.8:0.3:40:0.3,extrastereo=m=2.5,volume=1dB", 
    "live": "compand,aecho=0.8:0.88:60:0.2"
}

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

    # --- 1. Path Configuration ---
    base_path = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits")
    source_dir = base_path / "rain_content" / "recorded" / "enhanced"
    asset_dir = base_path / "rain_content" / "attachments" / "long"
    output_dir = base_path / "output" / "output_long"

    output_dir.mkdir(parents=True, exist_ok=True)
    img_logo_path = asset_dir / "screen-logo.png"

    # --- 2. Selection ---
    video_input = select_video_file(source_dir)
    rain_input = select_audio_file(base_path / "input" / "audio_pools" / "rain")
    if not video_input or not rain_input:
        return

    sfx_input = select_optional_file(base_path / "input" / "audio_pools" / "sfx", "Secondary SFX")
    music_input = select_optional_file(base_path / "input" / "audio_pools" / "music", "Tertiary Music")

    # --- 3. Phase Logic ---
    print("\n--- Phase Allocation (Total must be 100%) ---")
    p1_pct = float(input("Phase 1: Ultra Quality %: ") or 100)

    if p1_pct >= 100:
        p2_pct, p3_pct = 0, 0
    else:
        p2_pct = float(input(f"Phase 2: Dark Fade % (Remaining {100 - p1_pct}%): ") or 0)
        p3_pct = max(0, 100 - p1_pct - p2_pct)

    print(f">> Final Split: P1: {p1_pct}% | P2: {p2_pct}% | P3: {p3_pct}%")

    # --- 4. Runtime ---
    target_minutes = float(input("\nEnter DESIRED final length (Minutes): "))
    total_seconds = int(target_minutes * 60)

    p2_start = (p1_pct / 100) * total_seconds
    p2_duration = (p2_pct / 100) * total_seconds
    p3_start = p2_start + p2_duration

    fade_duration = max(p2_duration, 0.1)

    res_map = {
        "480p": "854:480",
        "720p": "1280:720",
        "1080p": "1920:1080",
        "2k": "2560:1440",
        "4k": "3840:2160"
    }

    res_choice = input("Resolution (4k, 2k, 1080p, 720p): ").lower().strip()
    target_res = res_map.get(res_choice, "3840:2160")
    w, h = target_res.split(':')

    final_output = output_dir / f"Rain_Phase_Video_{int(target_minutes)}m.mp4"

    # --- 5A. VIDEO FILTER (FIXED) ---
    font_path = "C\\\\:/Windows/Fonts/arial.ttf"

    filter_v = (
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},setsar=1,"
        f"fade=t=out:st={p2_start}:d={fade_duration}:color=black[v_faded];"

        f"[v_faded]drawbox=x=0:y=0:w=iw:h=ih:color=black:"
        f"thickness=fill:enable='gte(t,{p3_start})'[v_dark];"

        f"[1:v]scale={w}:{h}[logo];"
        f"[v_dark][logo]overlay=0:0:enable='between(t,5,{p2_start})'[v_logo];"

        f"[v_logo]drawtext=text='Calm Rain':"
        f"fontfile='{font_path}':"
        f"fontsize=40:fontcolor=white@0.5:"
        f"x='w-mod(t*60,w+text_w)':y=h-100:"
        f"enable='between(t,5,{p2_start})'[vout]"
    )

    # --- 5B. AUDIO FILTER (SAFE EXPRESSIONS) ---
    fade_denom = max(p2_duration, 0.1)

    vol_clean = f"max(1-(t-{p2_start})/{fade_denom},0)"
    vol_muff = f"min((t-{p2_start})/{fade_denom},1)"
    vol_brn = f"min(0.12*(t-{p2_start})/{fade_denom},0.12)"

    audio_inputs = ["-stream_loop", "-1", "-i", str(rain_input)]

    filter_a = (
        f"anoisesrc=d={total_seconds}:c=brown:r=44100,"
        f"volume='{vol_brn}':eval=frame[brn_layer];"
        f"[2:a]bass=g=5:f=100,volume=0.8[rain_p];"
    )

    mix_srcs = ["[rain_p]"]
    idx = 3

    if sfx_input:
        audio_inputs += ["-stream_loop", "-1", "-i", str(sfx_input)]
        filter_a += f"[{idx}:a]volume=0.15[sfx_p];"
        mix_srcs.append("[sfx_p]")
        idx += 1

    if music_input:
        audio_inputs += ["-stream_loop", "-1", "-i", str(music_input)]
        filter_a += f"[{idx}:a]volume=0.10[music_p];"
        mix_srcs.append("[music_p]")
        idx += 1

    filter_a += (
        f"{''.join(mix_srcs)}amix=inputs={len(mix_srcs)}:duration=first[full_mix];"
        f"[full_mix]asplit=2[clean][muff];"
        f"[muff]lowpass=f=350[muff_lp];"
        f"[clean]volume='{vol_clean}':eval=frame[clean_faded];"
        f"[muff_lp]volume='{vol_muff}':eval=frame[muff_faded];"
        f"[clean_faded][muff_faded][brn_layer]amix=inputs=3:weights='1 1 1'[final_a]"
    )

    # --- 6. COMMAND ---
    print(f"\n[Executing] Rendering {target_minutes}m Phase-Shifted Content...")

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(video_input),
        "-i", str(img_logo_path),
    ] + audio_inputs + [
        "-filter_complex", f"{filter_v};{filter_a}",
        "-map", "[vout]",
        "-map", "[final_a]",
        "-t", str(total_seconds),
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "320k",
        str(final_output)
    ]

    subprocess.run(cmd, check=True)

    print(f"\n✅ SUCCESS! File created: {final_output}")

    # ---------------------------
    # 1. PATH SETUP
    # ---------------------------
    base_path = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits")
    source_dir = base_path / "rain_content" / "recorded" / "enhanced"
    asset_dir = base_path / "rain_content" / "attachments" / "long"
    output_dir = base_path / "output" / "output_long"
    output_dir.mkdir(parents=True, exist_ok=True)

    img_logo_path = asset_dir / "screen-logo.png"

    # ---------------------------
    # 2. INPUT SELECTION
    # ---------------------------
    print("\nSelect your main background video (looped automatically)")
    video_input = select_video_file(source_dir)

    print("\nSelect your PRIMARY rain audio (this drives the atmosphere)")
    rain_input = select_audio_file(base_path / "input" / "audio_pools" / "rain")

    if not video_input or not rain_input:
        print("❌ Missing required inputs. Aborting.")
        return

    print("\nOptional: Add texture layers to enrich realism")
    sfx_input = select_optional_file(base_path / "input" / "audio_pools" / "sfx", "Secondary SFX (e.g. roof, window)")
    music_input = select_optional_file(base_path / "input" / "audio_pools" / "music", "Background ambience/music")

    # ---------------------------
    # 3. PHASE DESIGN
    # ---------------------------
    print("\n--- Phase Design ---")
    print("Phase 1 = Full clarity")
    print("Phase 2 = Gradual fade to dark + muffled audio")
    print("Phase 3 = Fully dark + sleep state")

    p1_pct = float(input("Phase 1 (% of video, default 100): ") or 100)

    if p1_pct >= 100:
        p2_pct, p3_pct = 0, 0
    else:
        remaining = 100 - p1_pct
        p2_pct = float(input(f"Phase 2 (% of remaining {remaining}): ") or 0)
        p3_pct = max(0, 100 - p1_pct - p2_pct)

    print(f"Final Split → P1:{p1_pct}% | P2:{p2_pct}% | P3:{p3_pct}%")

    # ---------------------------
    # 4. DURATION
    # ---------------------------
    minutes = float(input("\nEnter final duration (minutes): "))
    total_seconds = int(minutes * 60)

    p2_start = (p1_pct / 100) * total_seconds
    p2_duration = max((p2_pct / 100) * total_seconds, 0.1)
    p3_start = p2_start + p2_duration

    # ---------------------------
    # 5. RESOLUTION
    # ---------------------------
    res_map = {
        "720p": "1280:720",
        "1080p": "1920:1080",
        "2k": "2560:1440",
        "4k": "3840:2160"
    }

    res = input("Resolution (720p,1080p,2k,4k): ").lower().strip()
    target_res = res_map.get(res, "2560:1440")
    w, h = target_res.split(":")

    output_file = output_dir / f"Rain_Phase_Video_{int(minutes)}m.mp4"

    # ---------------------------
    # 6. VIDEO FILTER (FIXED)
    # ---------------------------
    filter_v = (
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},setsar=1,"
        f"fade=t=out:st={p2_start}:d={p2_duration}:color=black[v1];"

        f"[v1]drawbox=x=0:y=0:w=iw:h=ih:color=black:"
        f"thickness=fill:enable=gte(t\\,{p3_start})[v2];"

        f"[1:v]scale={w}:{h}[logo];"
        f"[v2][logo]overlay=0:0:enable=between(t\\,5\\,{p2_start})[v3];"

        # FIXED drawtext (NO fontfile path issues)
        f"[v3]drawtext=text=Calm\\ Rain:"
        f"font=Arial:"
        f"fontsize=40:"
        f"fontcolor=white@0.5:"
        f"x=w-mod(t*60\\,w+text_w):"
        f"y=h-100:"
        f"enable=between(t\\,5\\,{p2_start})"
        f"[vout]"
    )

    # ---------------------------
    # 7. AUDIO FILTER (SAFE)
    # ---------------------------
    denom = max(p2_duration, 0.1)

    vol_clean = f"max(1-(t-{p2_start})/{denom},0)"
    vol_muff = f"min((t-{p2_start})/{denom},1)"
    vol_brn = f"min(0.12*(t-{p2_start})/{denom},0.12)"

    audio_inputs = ["-stream_loop", "-1", "-i", str(rain_input)]

    filter_a = (
        f"anoisesrc=d={total_seconds}:c=brown:r=44100,"
        f"volume='{vol_brn}':eval=frame[brn];"
        f"[2:a]bass=g=5:f=100,volume=0.8[rain];"
    )

    mix = ["[rain]"]
    idx = 3

    if sfx_input:
        audio_inputs += ["-stream_loop", "-1", "-i", str(sfx_input)]
        filter_a += f"[{idx}:a]volume=0.15[sfx];"
        mix.append("[sfx]")
        idx += 1

    if music_input:
        audio_inputs += ["-stream_loop", "-1", "-i", str(music_input)]
        filter_a += f"[{idx}:a]volume=0.10[music];"
        mix.append("[music]")
        idx += 1

    filter_a += (
        f"{''.join(mix)}amix=inputs={len(mix)}:duration=first[mix1];"
        f"[mix1]asplit=2[clean][muff];"
        f"[muff]lowpass=f=350[muff2];"
        f"[clean]volume='{vol_clean}':eval=frame[c];"
        f"[muff2]volume='{vol_muff}':eval=frame[m];"
        f"[c][m][brn]amix=inputs=3[final_a]"
    )

    # ---------------------------
    # 8. EXECUTION
    # ---------------------------
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(video_input),
        "-i", str(img_logo_path)
    ] + audio_inputs + [
        "-filter_complex", f"{filter_v};{filter_a}",
        "-map", "[vout]",
        "-map", "[final_a]",
        "-t", str(total_seconds),
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "320k",
        str(output_file)
    ]

    print("\nRendering video... This may take time depending on length.")
    subprocess.run(cmd, check=True)

    print(f"\n✅ SUCCESS → {output_file}")

def get_phase_configuration():
    """
    Collects and validates phase distribution from user.

    Returns:
        tuple: (p1_pct, p2_pct, p3_pct)
    """

    print("\n--- Phase Design Configuration ---")
    print("Define how the video transitions over time:")
    print("• Phase 1 → Full clarity (visual + audio)")
    print("• Phase 2 → Gradual fade to dark + muffled sound")
    print("• Phase 3 → Fully dark (sleep state)")
    print("NOTE: Total must not exceed 100%")

    while True:
        try:
            p1_pct = float(input("\nEnter Phase 1 percentage (default 100): ") or 100)

            if p1_pct >= 100:
                print("Phase 1 consumes entire timeline. No fade will occur.")
                return p1_pct, 0.0, 0.0

            remaining = 100 - p1_pct
            print(f"Remaining percentage available: {remaining:.2f}%")

            p2_pct = float(input(f"Enter Phase 2 percentage (≤ {remaining}): ") or 0)

            if p2_pct > remaining:
                print("❌ Phase 2 exceeds remaining allocation. Try again.")
                continue

            p3_pct = 100 - p1_pct - p2_pct

            print("\n✅ Final Phase Distribution:")
            print(f"• Phase 1: {p1_pct:.2f}%")
            print(f"• Phase 2: {p2_pct:.2f}%")
            print(f"• Phase 3: {p3_pct:.2f}%")

            return p1_pct, p2_pct, p3_pct

        except ValueError:
            print("❌ Invalid input. Please enter numeric values.")

def compute_timeline(p1_pct, p2_pct, p3_pct):
    """
    Computes timeline values based on phase percentages.

    Args:
        p1_pct (float)
        p2_pct (float)
        p3_pct (float)

    Returns:
        dict containing timeline values
    """

    print("\n--- Duration Setup ---")
    print("Specify how long the final rendered video should be.")

    while True:
        try:
            minutes = float(input("Enter total duration (minutes): "))
            if minutes <= 0:
                print("❌ Duration must be greater than 0.")
                continue

            total_seconds = int(minutes * 60)

            # Phase calculations
            p2_start = (p1_pct / 100) * total_seconds
            p2_duration = (p2_pct / 100) * total_seconds
            p3_start = p2_start + p2_duration

            # Safety guard (prevents division errors later)
            fade_duration = max(p2_duration, 0.1)

            print("\n✅ Timeline Computed:")
            print(f"• Total Duration: {total_seconds}s")
            print(f"• Phase 2 Start: {p2_start:.2f}s")
            print(f"• Phase 2 Duration: {p2_duration:.2f}s")
            print(f"• Phase 3 Start: {p3_start:.2f}s")

            return {
                "minutes": minutes,
                "total_seconds": total_seconds,
                "p2_start": p2_start,
                "p2_duration": p2_duration,
                "p3_start": p3_start,
                "fade_duration": fade_duration
            }

        except ValueError:
            print("❌ Invalid input. Please enter a numeric value.")

def process_long_content():
    # 1. Paths Configuration
    base_path = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits")
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

    # --- Phase & Duration Configuration ---
    p1, p2, p3 = get_phase_configuration()
    timeline = compute_timeline(p1, p2, p3)
    
    target_seconds = timeline["total_seconds"]
    formatted_time = format_duration(timeline["minutes"])

    # --- Runtime Inputs ---
    print("\n--- Social CTA Ticker ---")
    default_sub = "More rain content is on the way; Subscribe so you never miss a moment of calm"
    sub_text = input(f"Enter Ticker Text [Leave blank for default]: ").strip() or default_sub

    try:
        speed_factor = float(input("Enter Speed Factor [Default 1.0]: ") or 1.0)
        master_vol_pct = float(input("Final Output Volume % [Default 100]: ") or 100)
        master_gain = master_vol_pct / 100
        
        rain_vol = float(input("Rain Layer Volume % [Default 75]: ") or 75) / 100
        sfx_vol = float(input("SFX Layer Volume % [Default 15]: ") or 15) / 100 if sfx_input else 0.15
        music_vol = float(input("Music Layer Volume % [Default 10]: ") or 10) / 100 if music_input else 0.10
    except ValueError:
        speed_factor, master_gain, rain_vol, sfx_vol, music_vol = 1.0, 1.0, 0.75, 0.15, 0.10

    res_map = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080", "2k": "2560:1440", "4k": "3840:2160"}
    res_choice = input("\nEnter resolution (e.g., 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1920:1080")

    # --- Video Loop Logic ---
    duration, _ = get_video_info(video_input)
    adj_duration = duration * speed_factor
    loop_fade_dur = 1.0 
    loop_duration = adj_duration - loop_fade_dur 

    tile_file = output_dir / "temp_master_tile.mp4"
    segment_file = output_dir / "temp_1min_segment.mp4"
    temp_no_audio = output_dir / "temp_silent_final.mp4"
    list_file = output_dir / "concat_list.txt"
    final_output = output_dir / f"Rain_Video_{formatted_time.replace(' ', '_')}.mp4"

    try:
        # [1/4] Preparing Video Loop
        filter_tile = (
            f"[0:v]setpts={speed_factor}*PTS,"
            f"scale={target_res}:force_original_aspect_ratio=increase,crop={target_res},setsar=1,split[main][over];"
            f"[over]trim=start=0:end={loop_fade_dur},setpts=PTS-STARTPTS[fadein];"
            f"[main]trim=start={loop_fade_dur},setpts=PTS-STARTPTS[base];"
            f"[fadein]format=pix_fmts=yuva420p,fade=t=in:st=0:d={loop_fade_dur}:alpha=1[alpha_fade];"
            f"[base][alpha_fade]overlay=x=0:y=0:shortest=1[v]"
        )
        subprocess.run(["ffmpeg", "-y", "-i", str(video_input), "-filter_complex", filter_tile, "-map", "[v]", "-c:v", "libx264", "-crf", "18", str(tile_file)], check=True)

        with open(list_file, "w") as f:
            for _ in range(math.ceil(60 / loop_duration)): f.write(f"file '{tile_file.name}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", "-t", "60", str(segment_file)], check=True)

        # [2/4] Assembling Master with Video Fade
        print(f"[2/4] Assembling Master...")
        with open(list_file, "w") as f:
            for _ in range(math.ceil(timeline["minutes"])): f.write(f"file '{segment_file.name}'\n")

        scroll_speed = 50
        filter_final = (
            f"[1:v]scale={target_res}[logo_sc];"
            f"[0:v][logo_sc]overlay=0:0:enable='between(t,5,{timeline['p2_start']})'[v_logo];"
            f"[v_logo]drawbox=y=ih-80:color=black@0.6:width=iw:height=60:t=fill:enable='between(t,5,{timeline['p2_start']})'[v_bg];"
            f"[v_bg]drawtext=text='{sub_text}':font='Arial':fontsize=24:fontcolor=0x5cf629:"
            f"x='mod(t*{scroll_speed}, w+text_w)-text_w':y=h-62:enable='between(t,5,{timeline['p2_start']})':"            
            f"shadowcolor=black@0.8:shadowx=2:shadowy=2[v_elements];"
            f"[v_elements]fade=t=out:st={timeline['p2_start']}:d={timeline['fade_duration']}[vout]"
        )
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-i", str(img_logo_path), "-filter_complex", filter_final, "-map", "[vout]", "-t", str(target_seconds), "-c:v", "libx264", "-crf", "21", "-preset", "veryfast", str(temp_no_audio)], check=True)

        # [3/4] Blending Audio with Crossfade Muffling
        print(f"\n[3/4] Blending Audio with Muffling Phase...")
        
        profile_filter = AUDIO_PROFILES["long"] 
        audio_inputs = []
        filter_audio = ""
        mix_labels = ""
        
        layers = [
            (rain_input, rain_vol, "rain"),
            (sfx_input, sfx_vol, "sfx"),
            (music_input, music_vol, "music")
        ]
        
        active_layers = [l for l in layers if l[0]]
        
        for idx, (path, vol, name) in enumerate(active_layers):
            audio_inputs += ["-stream_loop", "-1", "-i", str(path)]
            
            # FIX: Create two paths: one clear, one muffled, and fade between them
            filter_audio += (
                f"[{idx+1}:a]{profile_filter},volume={vol},highpass=f=20,asplit=2[clr_{name}][muf_{name}];"
                f"[muf_{name}]lowpass=f=400[muf_final_{name}];"
                f"[clr_{name}]afade=t=out:st={timeline['p2_start']}:d={timeline['fade_duration']}[clr_fade_{name}];"
                f"[muf_final_{name}]afade=t=in:st={timeline['p2_start']}:d={timeline['fade_duration']}[muf_fade_{name}];"
                f"[clr_fade_{name}][muf_fade_{name}]amix=inputs=2:duration=first[merged_{name}];"
                f"[merged_{name}]afade=t=in:st=0:d=0.1,afade=t=out:st={target_seconds-0.1}:d=0.1[{name}];"
            )
            mix_labels += f"[{name}]"

        filter_audio += (
            f"{mix_labels}amix=inputs={len(active_layers)}:duration=first:dropout_transition=3:normalize=0[a_mixed];"
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

        print(f"\n✅ SUCCESS! {formatted_time} video created.")

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
    Produces R, C, and L shorts with seamless composite audio and 
    Matching-Pair JSON metadata files with Master Volume Control.
    """
    # --- 1. Path Configurations ---
    base_path = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits")
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
    dur_raw = input("\nTarget Duration (e.g., 59) [Default 59s]: ").strip().lower()
    target_seconds = float(dur_raw.replace('m', '')) * 60 if 'm' in dur_raw else float(dur_raw or 59)

    res_map = {"720p": "720:1280", "1080p": "1080:1920", "2k": "1440:2560", "4k": "2160:3840"}
    res_choice = input("Enter resolution (default 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1080:1920")
    t_w, t_h = map(int, target_res.split(':'))

    # --- 5. Volume Balancing ---
    try:
        master_vol_pct = float(input("Master Output Volume % [Default 100]: ") or 100)
        master_gain = master_vol_pct / 100
        rain_vol = float(input("Rain Volume % [Default 75]: ") or 75) / 100
        brown_vol = 0.05 
        sfx_vol = float(input("SFX Volume % [Default 15]: ") or 15) / 100 if sfx_input else 0.15
        music_vol = float(input("Music Volume % [Default 10]: ") or 10) / 100 if music_input else 0.10
    except ValueError:
        master_gain, rain_vol, brown_vol, sfx_vol, music_vol = 1.0, 0.75, 0.05, 0.15, 0.10

    configs = {
        "Right": {"profile": "short_r", "offset": "in_w-out_w"},
        "Center": {"profile": "short_c", "offset": "(in_w-out_w)/2"},
        "Left": {"profile": "short_l", "offset": "0"}
    }

    # --- 6. Batch Processing Loop ---
    short_index = 0
    for label, cfg in configs.items():
        if short_index >= len(master_metadata): break

        current_seo = master_metadata[short_index]
        raw_title = current_seo.get("title", "Untitled_Short")
        base_name = f"{sanitize_filename(raw_title)}_{label}"
        video_output = output_dir / f"{base_name}.mp4"
        json_output = output_dir / f"{base_name}.json"

        print(f"\n🎬 Rendering Seamless {label}: {base_name}")
        
        sub_start, sub_end = max(0, target_seconds - 10), target_seconds
        font_path = "C\\:/Windows/Fonts/arialbd.ttf"
        caption = raw_title.replace("'", "\\'").replace(":", "\\:")

        # Visual Filter (Stays standard)
        filter_v = (
            f"[0:v]scale=-1:{t_h},crop={t_w}:{t_h}:{cfg['offset']}:0,setsar=1,"
            f"drawtext=fontfile='{font_path}':text='{caption}':fontcolor=white:fontsize=90:"
            f"x=(w-text_w)/2:y=h*0.1:borderw=4:bordercolor=black[v_text];"
            f"[1:v]scale={t_w}:{t_h}[logo_scaled];"
            f"[v_text][logo_scaled]overlay=0:0[v_logo];"
            f"[2:v]scale={t_w}:{t_h}[sub_scaled];"
            f"[v_logo][sub_scaled]overlay=0:0:enable='between(t,{sub_start},{sub_end})'[v]"
        )

        # SEAMLESS AUDIO LOGIC:
        # 1. Use highpass/lowpass to remove frequency 'snaps' at loop points.
        # 2. Use tiny afade to smooth the junction.
        audio_inputs = ["-stream_loop", "-1", "-i", str(rain_input)]
        
        # Audio Base (Rain + Brown Noise)
        filter_a = (
            f"anoisesrc=d={target_seconds}:c=brown:r=44100,volume={brown_vol}[brn];"
            f"[3:a]volume={rain_vol},highpass=f=20,lowpass=f=18000,"
            f"afade=t=in:st=0:d=0.1,afade=t=out:st={target_seconds-0.1}:d=0.1[rain];"
        )
        mix_labels = "[rain][brn]"
        mix_count = 2 

        if sfx_input:
            audio_inputs += ["-stream_loop", "-1", "-i", str(sfx_input)]
            filter_a += (
                f"[{3 + (mix_count-1)}:a]volume={sfx_vol},highpass=f=20,"
                f"afade=t=in:st=0:d=0.1,afade=t=out:st={target_seconds-0.1}:d=0.1[sfx];"
            )
            mix_labels += "[sfx]"
            mix_count += 1
        
        if music_input:
            audio_inputs += ["-stream_loop", "-1", "-i", str(music_input)]
            filter_a += (
                f"[{3 + (mix_count-1)}:a]volume={music_vol},highpass=f=20,"
                f"afade=t=in:st=0:d=0.1,afade=t=out:st={target_seconds-0.1}:d=0.1[music];"
            )
            mix_labels += "[music]"
            mix_count += 1

        # FINAL CHAIN: Mix -> Master Volume -> Apply Specific Audio Profile
        filter_a += (
            f"{mix_labels}amix=inputs={mix_count}:duration=first:dropout_transition=2:normalize=0[a_mixed];"
            f"[a_mixed]volume={master_gain}[a_mastered];"
            f"[a_mastered]{AUDIO_PROFILES[cfg['profile']]}[final_a]"
        )

        try:
            subprocess.run([
                "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(video_input),
                "-i", str(asset_dir / "logo-cta.png"),
                "-i", str(asset_dir / "subscribe-cta.png")
            ] + audio_inputs + [
                "-filter_complex", f"{filter_v};{filter_a}",
                "-map", "[v]", "-map", "[final_a]",
                "-t", str(target_seconds),
                "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "192k", str(video_output)
            ], check=True)

            with open(json_output, 'w', encoding='utf-8') as jf:
                json.dump(current_seo, jf, indent=2)
            
            short_index += 1
            print(f"✅ Success: {video_output.name}")

        except subprocess.CalledProcessError:
            print(f"❌ FFmpeg failed on {label} variant.")
            continue

    print(f"\n✨ Batch complete. Results in: {output_dir}")

if __name__ == "__main__":
    print("--- CONTENT GENERATION TOOLKIT (FFMPEG NATIVE AUDIO) ---")
    print("1. Long | 2. Shorts Batch")
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