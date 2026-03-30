import subprocess
import json
import math
import os
from pathlib import Path

# --- CORE UTILITY FUNCTIONS ---

def get_video_info(video_path):
    """Retrieves duration and frame rate precisely."""
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
    """Lists mp3 files for user selection from a specific directory."""
    audio_files = list(audio_dir.glob("*.mp3"))
    if not audio_files:
        print(f"❌ No MP3 files found in {audio_dir}")
        return None
    
    print(f"\n🎵 Available Audio Tracks in {audio_dir.name}:")
    for i, file in enumerate(audio_files, 1):
        print(f"{i}. {file.name}")
    
    while True:
        try:
            choice = int(input("\nSelect audio number: "))
            if 1 <= choice <= len(audio_files):
                return audio_files[choice - 1]
            print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

# --- PROCESSING MODULES ---

def select_video_file(video_dir):
    """Lists mp4 files for user selection from a specific directory."""
    video_files = list(video_dir.glob("*.mp4"))
    if not video_files:
        print(f"❌ No MP3 files found in {video_dir}")
        return None
    
    print(f"\n📺 Available Source Videos in {video_dir.name}:")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file.name}")
    
    while True:
        try:
            choice = int(input("\nSelect video number: "))
            if 1 <= choice <= len(video_files):
                return video_files[choice - 1]
            print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

def process_long_content():
    """Handles Long-form horizontal content with overlays, video selection, and audio choice."""
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_long")
    audio_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\sounds")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Select Source Video (New Choice)
    video_input = select_video_file(source_dir)
    if not video_input: return

    # 2. Select Audio Choice
    audio_path = select_audio_file(audio_base_dir)
    if not audio_path: return

    # Image Assets
    asset_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\long")
    img1_path = asset_dir / "screen-cta.png"
    img2_path = asset_dir / "screen-logo.png"
    img3_path = asset_dir / "end-screen-cta.png"

    res_map = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080", "2k": "2560:1440", "4k": "3840:2160"}
    res_choice = input("\nEnter resolution (e.g., 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1920:1080")
    
    try:
        target_minutes = int(input("Enter length in MINUTES (4mins yields 1min content): "))
        target_seconds = target_minutes * 60
    except ValueError:
        print("Invalid minutes.")
        return

    tile_file = output_dir / "temp_master_tile.mp4"
    segment_file = output_dir / "temp_1min_segment.mp4"
    temp_no_audio = output_dir / "temp_silent_final.mp4"
    list_file = output_dir / "concat_list.txt"
    final_output = output_dir / f"Final_Long_{res_choice}_{target_minutes}min.mp4"

    try:
        duration, fps = get_video_info(video_input)
        fade_dur = 1.0 if duration > 3 else 0.5
        loop_duration = duration - fade_dur

        print(f"\n[1/4] Creating Seamless Tile from {video_input.name}...")
        filter_tile = (f"[0:v]scale={target_res}:force_original_aspect_ratio=increase,crop={target_res},setsar=1,split[main][over];"
                       f"[over]trim=start=0:end={fade_dur},setpts=PTS-STARTPTS[fadein];"
                       f"[main]trim=start={fade_dur},setpts=PTS-STARTPTS[base];"
                       f"[fadein]format=pix_fmts=yuva420p,fade=t=in:st=0:d={fade_dur}:alpha=1[alpha_fade];"
                       f"[base][alpha_fade]overlay=x=0:y=0:shortest=1[v]")
        
        subprocess.run(["ffmpeg", "-y", "-i", str(video_input), "-filter_complex", filter_tile, "-map", "[v]", "-r", str(fps), "-c:v", "libx264", "-crf", "18", str(tile_file)], check=True)

        print("[2/4] Building segments...")
        tiles_needed = math.ceil(60 / loop_duration)
        with open(list_file, "w") as f:
            for _ in range(tiles_needed): f.write(f"file '{tile_file.name}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", "-t", "60", str(segment_file)], check=True)

        print("[3/4] Final Assembly with Overlays...")
        with open(list_file, "w") as f:
            for _ in range(target_minutes): f.write(f"file '{segment_file.name}'\n")

        limit_time = target_seconds - 600
        img1_en = f"lt(mod(t,600),10)*lt(t,{limit_time})*gt(t,599)"
        img2_en = f"lt(t,{target_seconds - 60})"
        img3_en = f"gt(t,{target_seconds - 30})"

        filter_final = (f"[1:v]scale={target_res}[i1];[2:v]scale={target_res}[i2];[3:v]scale={target_res}[i3];"
                        f"[0:v][i1]overlay=0:0:enable='{img1_en}'[v1];"
                        f"[v1][i2]overlay=0:0:enable='{img2_en}'[v2];"
                        f"[v2][i3]overlay=0:0:enable='{img3_en}'[vout]")

        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-i", str(img1_path), "-i", str(img2_path), "-i", str(img3_path),
                        "-filter_complex", filter_final, "-map", "[vout]", "-t", str(target_seconds), "-c:v", "libx264", "-crf", "22", str(temp_no_audio)], check=True)

        print(f"[4/4] Adding Audio: {audio_path.name}")
        subprocess.run(["ffmpeg", "-y", "-i", str(temp_no_audio), "-stream_loop", "-1", "-i", str(audio_path), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", str(final_output)], check=True)
        print(f"✅ Success: {final_output}")

    except Exception as e:
        print(f"❌ Error during processing: {e}")
    finally:
        for f in [tile_file, segment_file, list_file, temp_no_audio]: 
            if f.exists(): f.unlink()

def process_shorts_batch():
    """Produces R, C, and L shorts at once with unique filenames, captions, and source video choice."""
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_shorts")
    audio_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\sounds")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Select Source Video for the batch
    video_input = select_video_file(source_dir)
    if not video_input: return

    # 2. Select Audio track for the batch
    audio_path = select_audio_file(audio_base_dir)
    if not audio_path: return

    asset_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\shorts")
    img1_path = asset_dir / "subscribe-cta.png"
    img2_path = asset_dir / "logo-cta.png"

    res_map = {"720p": "720:1280", "1080p": "1080:1920", "2k": "1440:2560", "4k": "2160:3840"}
    res_choice = input("\nEnter resolution (default 1080p): ").lower().strip()
    target_res = res_map.get(res_choice, "1080:1920")
    t_w, t_h = map(int, target_res.split(':'))

    _, fps = get_video_info(video_input)

    # Processing order: Right, Center, Left
    crops = {"R": "in_w-out_w", "C": "(in_w-out_w)/2", "L": "0"}

    for label, x_offset in crops.items():
        print(f"\n--- Configuring {label} (Right/Center/Left) version ---")
        
        # Request specific filename
        custom_filename = input(f"📁 Enter output filename for {label} version (e.g., rain_short_1): ").strip()
        if not custom_filename.lower().endswith(".mp4"):
            custom_filename += ".mp4"
            
        # Request unique caption
        user_caption = input(f"💬 Enter caption for {label} version: ").strip()
        
        final_output = output_dir / custom_filename
        
        print(f"🎬 Rendering {label} version using: {video_input.name}...")
        
        filter_complex = (
            f"[0:v]scale=-1:{t_h},crop={t_w}:{t_h}:{x_offset}:0,setsar=1,"
            f"drawtext=text='{user_caption}':font='Arial Black':fontcolor=white:fontsize=90:"
            f"x=(w-text_w)/2:y=h*0.1:borderw=4:bordercolor=black:fix_bounds=1[base];"
            f"[1:v]scale={t_w}:{t_h}[i1];[2:v]scale={t_w}:{t_h}[i2];"
            f"[base][i1]overlay=0:0:enable='between(t,10,15)'[temp];"
            f"[temp][i2]overlay=0:0:enable='1'[vout]"
        )

        try:
            subprocess.run([
                "ffmpeg", "-y", 
                "-i", str(video_input), 
                "-i", str(img1_path), 
                "-i", str(img2_path), 
                "-ss", "0", "-i", str(audio_path),
                "-filter_complex", filter_complex, 
                "-map", "[vout]", 
                "-map", "3:a", 
                "-t", "20", 
                "-c:v", "libx264", "-preset", "ultrafast", 
                "-c:a", "aac", "-b:a", "192k",
                str(final_output)
            ], check=True)
            print(f"✅ Saved: {custom_filename}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error rendering {custom_filename}: {e}")
    
    print(f"\n✨ Batch Complete! Check your files in: {output_dir}")

def process_live_content():
    """Handles both Horizontal and Vertical long-form content with custom naming."""
    # 1. Path Configurations
    source_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced")
    audio_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\attachments\sounds")
    output_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_live")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Source Selection (Video & Audio)
    video_input = select_video_file(source_dir)
    if not video_input: return

    audio_path = select_audio_file(audio_base_dir)
    if not audio_path: return

    # 3. Dynamic Output Filename
    print("\n💾 File Configuration:")
    custom_filename = input("Enter output filename (e.g., heavy_rain_ambient): ").strip()
    if not custom_filename.lower().endswith(".mp4"):
        custom_filename += ".mp4"

    # 4. Aspect Ratio & Resolution Choice
    print("\n📐 Select Aspect Ratio:")
    print("1. Horizontal (16:9)")
    print("2. Vertical (9:16)")
    ar_choice = input("Selection (1-2): ").strip()

    res_choice = input("\nEnter resolution (e.g., 1080p, 4k): ").lower().strip()
    
    h_res = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080", "2k": "2560:1440", "4k": "3840:2160"}
    v_res = {"480p": "480:854", "720p": "720:1280", "1080p": "1080:1920", "2k": "1440:2560", "4k": "2160:3840"}

    # 5. Handle Cropping Logic
    crop_filter = ""
    if ar_choice == '2':
        target_res = v_res.get(res_choice, "1080:1920")
        t_w, t_h = target_res.split(':')
        print("\n✂️ Select Vertical Crop:")
        print("L: Left | C: Center | R: Right")
        crop_pos = input("Selection (L/C/R): ").upper().strip()
        
        crops = {"L": "0", "C": "(in_w-out_w)/2", "R": "in_w-out_w"}
        x_offset = crops.get(crop_pos, "(in_w-out_w)/2")
        crop_filter = f"scale=-1:{t_h},crop={t_w}:{t_h}:{x_offset}:0,setsar=1"
    else:
        target_res = h_res.get(res_choice, "1920:1080")
        crop_filter = f"scale={target_res}:force_original_aspect_ratio=increase,crop={target_res},setsar=1"

    # 6. Length Configuration
    try:
        # User requested reminder: 1min of loop yields 15sec of unique footage
        target_minutes = int(input("\nEnter length in MINUTES (Note: 4mins input yields 1min content): "))
        target_seconds = target_minutes * 60
    except ValueError: 
        print("Invalid input for minutes.")
        return

    # File Paths
    tile_file = output_dir / "temp_live_tile.mp4"
    segment_file = output_dir / "temp_live_1min.mp4"
    temp_no_audio = output_dir / "temp_live_silent.mp4"
    list_file = output_dir / "live_concat_list.txt"
    final_output = output_dir / custom_filename

    try:
        duration, fps = get_video_info(video_input)
        fade_dur = 1.0 if duration > 3 else 0.5
        loop_duration = duration - fade_dur

        # Stage 1: Create Seamless Tile
        print(f"\n[1/4] Generating Seamless {res_choice} Tile...")
        filter_tile = (f"[0:v]{crop_filter},split[main][over];"
                       f"[over]trim=start=0:end={fade_dur},setpts=PTS-STARTPTS[fadein];"
                       f"[main]trim=start={fade_dur},setpts=PTS-STARTPTS[base];"
                       f"[fadein]format=pix_fmts=yuva420p,fade=t=in:st=0:d={fade_dur}:alpha=1[alpha_fade];"
                       f"[base][alpha_fade]overlay=x=0:y=0:shortest=1[v]")
        
        subprocess.run(["ffmpeg", "-y", "-i", str(video_input), "-filter_complex", filter_tile, 
                        "-map", "[v]", "-r", str(fps), "-c:v", "libx264", "-crf", "18", str(tile_file)], check=True)

        # Stage 2: Build 1-min segment
        print("[2/4] Building 1-minute segment...")
        tiles_needed = math.ceil(60 / loop_duration)
        with open(list_file, "w") as f:
            for _ in range(tiles_needed): f.write(f"file '{tile_file.name}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", "-t", "60", str(segment_file)], check=True)

        # Stage 3: Assemble Full Length
        print(f"[3/4] Assembling {target_minutes} minute loop...")
        with open(list_file, "w") as f:
            for _ in range(target_minutes): f.write(f"file '{segment_file.name}'\n")
        
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), 
                        "-c", "copy", "-t", str(target_seconds), str(temp_no_audio)], check=True)

        # Stage 4: Audio Finalization
        print(f"[4/4] Adding Audio: {audio_path.name}")
        subprocess.run(["ffmpeg", "-y", "-i", str(temp_no_audio), "-stream_loop", "-1", "-i", str(audio_path), 
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final_output)], check=True)
        
        print(f"✅ Success! Video saved as: {final_output}")

    finally:
        for f in [tile_file, segment_file, list_file, temp_no_audio]: 
            if f.exists(): f.unlink()

# --- MAIN RUNTIME ---

if __name__ == "__main__":
    print("--- CONTENT GENERATION TOOLKIT ---")
    print("1. Long (Horizontal + Overlays)")
    print("2. Shorts (Batch R, C, L versions)")
    print("3. Live (Vertical Long + Audio Select)")
    
    choice = input("\nSelect content type (1-3): ").strip()

    if choice == '1': process_long_content()
    elif choice == '2': process_shorts_batch()
    elif choice == '3': process_live_content()
    else: print("Invalid selection.")