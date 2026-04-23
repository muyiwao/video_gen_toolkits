import subprocess
import os
import json
import re
import shutil
from pathlib import Path
import sys
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips
import moviepy.video.fx as vfx 

# Adds the project root to the python path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from scripts import generate_thumbnail

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

# --- NEW UTILITY FOR AUDIO CLEANUP ---
def silence_banned_phrases(clip):
    """
    Replaces the first 1.5s of audio with a 'NEXT' voiceover.
    Ensure 'next_voiceover.mp3' exists in your assets folder.
    """
    if clip.audio is None:
        return clip
    
    duration = clip.duration
    if duration <= 1.5:
        return clip.without_audio()

    # 1. Get the 'Clean' part of the original audio
    original_clean_audio = clip.audio.subclipped(1.5, duration).with_start(1.5)
    
    # 2. Try to load the 'NEXT' replacement audio
    replacement_path = BASE_PATH / "edu_content" / "assets" / "next_voiceover.mp3"
    
    if replacement_path.exists():
        # Load replacement and ensure it doesn't exceed the 1.5s window
        next_audio = AudioFileClip(str(replacement_path)).subclip(0, 1.5)
        
        # Combine: [NEXT (0-1.5s)] + [Original (1.5s+)]
        combined_audio = CompositeAudioClip([next_audio, original_clean_audio])
        return clip.with_audio(combined_audio)
    else:
        print(f"⚠️ Replacement audio not found at {replacement_path}. Falling back to silence.")
        return clip.with_audio(original_clean_audio)

def merge_sequential_lessons(input_dir, output_filename="merged_output.mp4", target_res=(1280, 720)):
    """
    Merges numbered videos with high-resolution output and automated audio cleaning.
    """
    input_path = Path(input_dir)
    output_path = input_path / output_filename
    
    TRANSITION_DURATION = 0.5  
    NUMBER_DURATION = 2
    FONT_SIZE = 200

    # 1. Gather and sort files
    video_files = [f for f in input_path.glob("*.mp4") if f.stem.isdigit()]
    video_files.sort(key=lambda x: int(x.stem))

    if not video_files:
        print(f"⚠️ No numbered MP4 files found in {input_dir}"); return None

    # 2. Runtime Options
    print("\n--- Merge Configuration ---")
    print("1. Clean Merge (No Slides) | 2. Transition Slides (Numbers)")
    merge_type = input("Select Type: ").strip()
    
    print("3. Simple Cut (Fast) | 4. Crossfade (Smooth)")
    transition_choice = input("Select Style: ").strip()
    
    use_transitions = (merge_type == "2")
    apply_crossfade = (transition_choice == "4")

    processed_clips = []

    # 3. Process Each Clip
    for file_path in video_files:
        print(f"🎬 Processing: {file_path.name}")
        video_clip = VideoFileClip(str(file_path)).resized(target_res)
        
        # Apply the silence filter
        video_clip = silence_banned_phrases(video_clip)

        # Handle Number Slides
        if use_transitions:
            number_text = TextClip(
                text=file_path.stem,
                font_size=FONT_SIZE,
                color="white",
                size=target_res,
                font="Arial"
            ).with_duration(NUMBER_DURATION)
            
            number_slide = CompositeVideoClip([number_text.with_position("center")], size=target_res)
            
            if apply_crossfade:
                number_slide = number_slide.with_effects([
                    vfx.FadeIn(duration=TRANSITION_DURATION), 
                    vfx.FadeOut(duration=TRANSITION_DURATION)
                ])
            processed_clips.append(number_slide)
        
        # Handle Video Transitions
        if apply_crossfade:
            video_clip = video_clip.with_effects([
                vfx.FadeIn(duration=TRANSITION_DURATION), 
                vfx.FadeOut(duration=TRANSITION_DURATION)
            ])
            
        processed_clips.append(video_clip)

    # 4. Final Concatenation
    # padding < 0 creates the overlap required for the crossfade effect
    padding = -TRANSITION_DURATION if apply_crossfade else 0
    final_video = concatenate_videoclips(processed_clips, method="compose", padding=padding)

    # 5. Render
    final_video.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=30,
        logger="bar"
    )

    print(f"✨ SUCCESS: {output_path}")
    return output_path

def parse_selection(selection_str):
    """Parses strings like '1, 2-5, 10' into a sorted list of unique integers."""
    indices = set()
    # Split by comma and clean whitespace
    parts = [p.strip() for p in selection_str.split(',')]
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            indices.update(range(start, end + 1))
        elif part.isdigit():
            indices.add(int(part))
    return sorted(list(indices))

def run_shorts_batch(category, speed, caption, scale):
    """Processes specific user-selected videos and exports matching JSON metadata."""
    output_dir = BASE_PATH / "output" / "output_shorts"
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = BASE_PATH / "edu_content" / "attachments" / category / "shorts"
    
    # 1. Selection Input
    print("\n--- Batch Selection ---")
    print("Example: '1' or '1, 3-5' or '10-20'")
    selection_input = input("Enter video numbers to process: ").strip()
    selected_nums = parse_selection(selection_input)
    
    # 2. Theme Logic
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

    print(f"\n🚀 Preparing to process {len(selected_nums)} videos...")

    for num in selected_nums:
        # Construct path for files named 1.mp4, 2.mp4, etc.
        video_path = MAIN_V_DIR / f"{num}.mp4"
        
        if not video_path.exists():
            print(f"⚠️ Warning: {video_path.name} not found in pool. Skipping.")
            continue

        # metadata is 0-indexed, so 1.mp4 = index 0
        meta_index = num - 1
        if meta_index >= len(master_metadata):
            print(f"⚠️ Warning: No metadata found for video {num}. Skipping.")
            continue
            
        seo_package = master_metadata[meta_index]
        raw_title = seo_package.get("title", "Untitled")
        safe_name = sanitize_filename(raw_title)
        
        # --- Matching-Pair Naming Convention ---
        out_v = output_dir / f"{safe_name}.mp4"
        out_j = output_dir / f"{safe_name}.json"
        
        W, H = 1080, 1920
        target_w = int(W * (scale / 100))
        pts_val = 1.0 / speed
        
        # Calculate timing
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
            print(f"\n🎬 [{num}] Processing: {video_path.name} -> {safe_name}.mp4")
            subprocess.run(cmd, check=True, capture_output=True)
            
            # --- METADATA EXPORT ---
            with open(out_j, 'w', encoding='utf-8') as jf:
                json.dump(seo_package, jf, indent=4)
                
            print(f"✅ Success: Video and Metadata saved for '{raw_title}'")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg Error on {video_path.name}: {e.stderr.decode()}")

    print(f"\n✨ Batch complete. Output saved to: {output_dir}")

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
        merge_sequential_lessons(MAIN_V_DIR, output_filename="merged_output.mp4")
        run_long_editor(cat, spd)
        generate_thumbnail.generate_thumbnail_with_caption()

    
    print("\n✨ Processing Complete.")