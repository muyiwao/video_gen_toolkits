import os
import numpy as np
from moviepy import VideoFileClip

def select_rain_video_terminal(rain_folder):
    """Lists available rain videos in the console and prompts for selection without opening windows."""
    print("\n--- Rain Overlay Selection ---")
    
    supported_exts = ('.mp4', '.avi', '.mov', '.mkv')
    if not os.path.exists(rain_folder):
        print(f"Rain folder not found: {rain_folder}")
        return None

    rain_files = [f for f in os.listdir(rain_folder) if f.lower().endswith(supported_exts)]
    
    if not rain_files:
        print("No rain asset videos found in your pool directory.")
        print("Continuing without rain overlay assets.")
        return None

    for idx, file_name in enumerate(rain_files, start=1):
        print(f"{idx}. {file_name}")
    print(f"{len(rain_files) + 1}. Skip rain overlay (Process video without assets)")

    try:
        choice = int(input(f"Select rain asset (1-{len(rain_files) + 1}): ").strip())
        if 1 <= choice <= len(rain_files):
            chosen_file = rain_files[choice - 1]
            return os.path.join(rain_folder, chosen_file)
        else:
            print("Skipping rain overlay.")
            return None
    except ValueError:
        print("Invalid input. Skipping rain overlay.")
        return None

def select_masking_method(video_name):
    """Prompts the user to select how the rain should be applied per individual file."""
    print(f"\n--- Masking & Environment Method for: {video_name} ---")
    print("0. Whole Screen (Standard overlay everywhere)")
    print("1. Motion-Based Rain Masking (Overlay ONLY where rain movement is detected)")
    
    choice = input("Select masking method (0 or 1): ").strip()
    if choice in ['0', '1']:
        return int(choice)
    else:
        print("Invalid choice. Defaulting to Whole Screen (0).")
        return 0

def select_processing_mode():
    """Prompts the user to select single or batch processing."""
    print("\n--- Processing Mode ---")
    print("1. Single Video (Process only the first available video)")
    print("2. Batch Processing (Process all videos in the directory)")
    
    choice = input("Select processing mode (1 or 2): ").strip()
    return choice if choice in ['1', '2'] else '1'

def process_video(source_video_path, output_video_path, rain_video_path):
    """Handles the frame-by-frame rendering for an individual video asset."""
    video_filename = os.path.basename(source_video_path)
    print(f"\nProcessing: {video_filename}")
    
    base_clip = VideoFileClip(source_video_path)
    
    if not rain_video_path:
        print("No overlay selected. Saving raw file to enhanced directory without changes.")
        base_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
        base_clip.close()
        return

    # Prompt user for masking method dynamically per file being processed
    mask_method = select_masking_method(video_filename)
    print(f"Applying overlay using Method {mask_method}...")

    rain_clip = VideoFileClip(rain_video_path)

    # Match duration configurations
    if rain_clip.duration < base_clip.duration:
        rain_clip = rain_clip.loop(duration=base_clip.duration)
    else:
        rain_clip = rain_clip.subclipped(0, base_clip.duration)

    # Match video dimensions
    rain_clip = rain_clip.resized(new_size=base_clip.size)
    opacity = 0.8

    def screen_blend_frames(get_frame, t):
        base_frame = get_frame(t).astype(np.float32) / 255.0
        rain_frame = rain_clip.get_frame(t).astype(np.float32) / 255.0
        
        # --- METHOD 1: MOTION-BASED RAIN DETECTION ---
        if mask_method == 1:
            prev_t = max(0.0, t - (1.0 / base_clip.fps)) if t > 0 else (1.0 / base_clip.fps)
            prev_frame = get_frame(prev_t).astype(np.float32) / 255.0
            
            frame_diff = np.abs(base_frame - prev_frame)
            motion_map = (frame_diff[:, :, 0] * 0.299 + 
                          frame_diff[:, :, 1] * 0.587 + 
                          frame_diff[:, :, 2] * 0.114)
            
            motion_threshold = 0.08 
            motion_mask = np.where(motion_map > motion_threshold, 1.0, 0.0)
            motion_mask = np.expand_dims(motion_mask, axis=2)
            
            rain_frame = rain_frame * opacity * motion_mask

        # --- METHOD 0: WHOLE SCREEN ---
        else:
            rain_frame = rain_frame * opacity

        # Screen Blend Math
        blended = 1.0 - (1.0 - base_frame) * (1.0 - rain_frame)
        return (np.clip(blended, 0.0, 1.0) * 255.0).astype(np.uint8)

    final_video = base_clip.transform(screen_blend_frames)
    final_video.write_videofile(
        output_video_path, 
        codec="libx264", 
        audio_codec="aac",
        fps=base_clip.fps
    )
    
    base_clip.close()
    rain_clip.close()
    final_video.close()
    print(f"Saved: {output_video_path}")

def overlay_rain():
    RAIN_POOL_DIR = r"C:\Project_Works\MuyProjects\video_gen_toolkits\input\video_pools"
    INPUT_DIR = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\second_processed"
    OUTPUT_DIR = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\final_processed"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    supported_exts = ('.mp4', '.avi', '.mov', '.mkv')
    input_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(supported_exts)]

    if not input_files:
        print(f"No source videos found in {INPUT_DIR}")
        return

    # 1. Choose Single vs Batch Mode
    proc_mode = select_processing_mode()
    
    # 2. Select rain video asset strictly using console interface
    rain_video_path = select_rain_video_terminal(RAIN_POOL_DIR)

    # 3. Execution Routing
    if proc_mode == '1':
        # Single Video Mode
        source_video_name = input_files[0]
        source_video_path = os.path.join(INPUT_DIR, source_video_name)
        output_video_path = os.path.join(OUTPUT_DIR, f"enhanced_{source_video_name}")
        
        process_video(source_video_path, output_video_path, rain_video_path)
    else:
        # Batch Video Mode
        print(f"\n--- Starting Batch Process ({len(input_files)} files found) ---")
        for index, source_video_name in enumerate(input_files, start=1):
            print(f"\n[{index}/{len(input_files)}]")
            source_video_path = os.path.join(INPUT_DIR, source_video_name)
            output_video_path = os.path.join(OUTPUT_DIR, f"enhanced_{source_video_name}")
            
            process_video(source_video_path, output_video_path, rain_video_path)
            
        print("\n--- Batch Processing Complete! ---")

if __name__ == "__main__":
    overlay_rain()