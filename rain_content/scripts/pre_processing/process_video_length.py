import ffmpeg
import os
import sys
from pathlib import Path

def process_video_length():
    # --- Configuration ---
    input_dir = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\raw")
    output_dir = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\first_processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Select Video
    video_files = sorted(list(input_dir.glob("*.mp4")))
    if not video_files:
        print(f"❌ No MP4 files found in {input_dir}")
        return

    print("\n--- Available Videos ---")
    for i, f in enumerate(video_files, 1):
        print(f"{i}. {f.name}")
    
    try:
        selection = input(f"\nSelect Video (1-{len(video_files)}): ")
        v_idx = int(selection) - 1
        input_file = video_files[v_idx]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return

    # 2. Get Metadata
    try:
        probe = ffmpeg.probe(str(input_file))
        duration_orig = float(probe['format']['duration'])
    except Exception as e:
        print(f"❌ Error probing video: {e}")
        return

    # 3. Runtime User Inputs
    try:
        target_len = float(input("Enter Target Duration (seconds): ").strip())
        req_speed = float(input("Enter Video Speed (default 1.0): ").strip() or 1.0)
    except ValueError:
        print("❌ Invalid number input.")
        return

    # 4. Recursive Speed Adjustment Logic
    def calculate_feasible_params(current_speed):
        effective_duration = duration_orig / current_speed
        
        if effective_duration < target_len:
            new_speed = duration_orig / target_len
            print(f"⚠️ Requested speed ({current_speed}x) makes video too short ({effective_duration:.2f}s).")
            print(f"🔄 Adjusting speed to {new_speed:.4f}x to achieve {target_len}s.")
            return new_speed
        return current_speed

    final_speed = calculate_feasible_params(req_speed)
    pts_value = 1.0 / final_speed

    output_file = output_dir / f"PROC_{target_len}s_{input_file.name}"

    print(f"\n🎬 Processing: Speed {final_speed:.2f}x | Muting Audio...")

    # 5. FFmpeg Execution
    try:
        # Define output parameters in a dictionary to handle the colon in 'c:v'
        output_args = {
            't': target_len,
            'an': None,         # Mute audio
            'c:v': 'libx264',   # Corrected colon usage
            'crf': 18,
            'preset': 'veryfast'
        }

        (
            ffmpeg
            .input(str(input_file))
            .video
            .filter('setpts', f"{pts_value}*PTS")
            .output(str(output_file), **output_args)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"✅ Success! Saved to: {output_file}")

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else "Unknown error"
        print(f"❌ FFmpeg Error: {error_msg}")

if __name__ == "__main__":
    process_video_length()