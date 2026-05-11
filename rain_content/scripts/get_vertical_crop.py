import ffmpeg
import os
import sys
from pathlib import Path

def get_vertical_crop():
    # --- Configuration ---
    input_dir = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\output\output_long")
    output_dir = input_dir / "vertical_shorts"
    output_dir.mkdir(exist_ok=True)

    # 1. Select Video from Directory
    video_files = sorted(list(input_dir.glob("*.mp4")))
    if not video_files:
        print(f"❌ No MP4 files found in {input_dir}")
        return

    print("\n--- Available Videos ---")
    for i, f in enumerate(video_files, 1):
        print(f"{i}. {f.name}")
    
    try:
        v_idx = int(input(f"\nSelect Video (1-{len(video_files)}): ")) - 1
        input_file = video_files[v_idx]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return

    # 2. Probe Video Dimensions
    try:
        probe = ffmpeg.probe(str(input_file))
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        in_w = int(video_stream['width'])
        in_h = int(video_stream['height'])
    except Exception as e:
        print(f"❌ Error probing video: {e}")
        return

    # 3. User Inputs for Crop and Duration
    print("\n--- Split Position ---")
    print("L: Left | C: Center | R: Right")
    pos_choice = input("Select (L/C/R) [Default C]: ").strip().upper() or "C"
    
    target_seconds = input("Target duration in seconds (e.g. 15, 60): ").strip()
    
    # 4. Calculate Logic
    # Vertical width is 9/16 of the current height
    target_w = int(in_h * (9/16))
    
    if pos_choice == 'L':
        x_offset = 0
    elif pos_choice == 'R':
        x_offset = in_w - target_w
    else: # Default Center
        x_offset = (in_w - target_w) // 2

    output_file = output_dir / f"SHORT_{pos_choice}_{input_file.name}"

    print(f"\n🎬 Rendering {target_w}x{in_h} vertical video at {pos_choice} offset...")
    
    # 5. FFmpeg Execution
    try:
        stream = ffmpeg.input(str(input_file))
        
        # Apply crop filter
        v = stream.video.filter('crop', target_w, in_h, x_offset, 0)
        a = stream.audio

        # Use a dictionary for arguments containing colons like 'c:v'
        output_params = {
            't': target_seconds,
            'c:v': 'libx264',
            'crf': 18,
            'preset': 'veryfast',
            'c:a': 'aac',
            'b:a': '192k'
        }

        (
            ffmpeg
            .output(v, a, str(output_file), **output_params)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"✅ Success! Saved to: {output_file}")

    except ffmpeg.Error as e:
        # Standard error usually contains the specific FFmpeg log
        error_msg = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
        print(f"❌ FFmpeg Error: {error_msg}")

if __name__ == "__main__":
    get_vertical_crop()