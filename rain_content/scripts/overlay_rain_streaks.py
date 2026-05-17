import os
import numpy as np
from moviepy import VideoFileClip
from PIL import Image

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
    print(f"{len(rain_files) + 1}. Skip rain overlay (Process asset without overlay)")

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

def select_masking_method(asset_name, is_image=False):
    """Prompts the user to select how the rain should be applied per individual file."""
    if is_image:
        print(f"\n--- Info for: {asset_name} ---")
        print("Asset is an image. Defaulting to Whole Screen overlay (Motion-based masking skipped).")
        return 0

    print(f"\n--- Masking & Environment Method for: {asset_name} ---")
    print("0. Whole Screen (Standard overlay everywhere)")
    print("1. Motion-Based Rain Masking (Overlay ONLY where rain movement is detected)")
    
    choice = input("Select masking method (0 or 1): ").strip()
    if choice in ['0', '1']:
        return int(choice)
    else:
        print("Invalid choice. Defaulting to Whole Screen (0).")
        return 0

def select_processing_mode(input_files):
    """Prompts the user to select single or batch processing, allowing file choice for single mode."""
    print("\n--- Processing Mode ---")
    print("1. Single File (Pick a specific image or video to process)")
    print("2. Batch Processing (Process all assets in the directory)")
    
    mode_choice = input("Select processing mode (1 or 2): ").strip()
    
    if mode_choice == '2':
        return '2', input_files

    # Single File Selection Flow
    print("\n--- Available Input Files ---")
    for idx, file_name in enumerate(input_files, start=1):
        print(f"{idx}. {file_name}")
        
    try:
        file_idx = int(input(f"Select file to process (1-{len(input_files)}): ").strip())
        if 1 <= file_idx <= len(input_files):
            # Return selection wrapped in a list to keep data mapping consistent
            return '1', [input_files[file_idx - 1]]
        else:
            print(f"Invalid selection. Defaulting to first file: {input_files[0]}")
            return '1', [input_files[0]]
    except ValueError:
        print(f"Invalid input. Defaulting to first file: {input_files[0]}")
        return '1', [input_files[0]]

def process_image(source_image_path, output_image_path, rain_video_path):
    """Extracts the first frame of the rain video and blends it onto the source image."""
    image_filename = os.path.basename(source_image_path)
    print(f"\nProcessing Image: {image_filename}")

    base_img = Image.open(source_image_path).convert("RGB")
    
    if not rain_video_path:
        print("No overlay selected. Saving raw image without changes.")
        base_img.save(output_image_path)
        return

    _ = select_masking_method(image_filename, is_image=True)

    rain_clip = VideoFileClip(rain_video_path)
    rain_frame_np = rain_clip.get_frame(0)
    rain_clip.close()

    base_arr = np.array(base_img).astype(np.float32) / 255.0
    
    rain_img = Image.fromarray(rain_frame_np).resize(base_img.size, Image.Resampling.LANCZOS)
    rain_arr = np.array(rain_img).astype(np.float32) / 255.0

    opacity = 0.8
    rain_arr = rain_arr * opacity

    blended = 1.0 - (1.0 - base_arr) * (1.0 - rain_arr)
    final_arr = (np.clip(blended, 0.0, 1.0) * 255.0).astype(np.uint8)

    final_img = Image.fromarray(final_arr)
    final_img.save(output_image_path)
    print(f"Saved Image: {output_image_path}")

def process_video(source_video_path, output_video_path, rain_video_path):
    """Handles the frame-by-frame rendering for an individual video asset."""
    video_filename = os.path.basename(source_video_path)
    print(f"\nProcessing Video: {video_filename}")
    
    base_clip = VideoFileClip(source_video_path)
    
    if not rain_video_path:
        print("No overlay selected. Saving raw file to enhanced directory without changes.")
        base_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
        base_clip.close()
        return

    mask_method = select_masking_method(video_filename, is_image=False)
    print(f"Applying overlay using Method {mask_method}...")

    rain_clip = VideoFileClip(rain_video_path)

    if rain_clip.duration < base_clip.duration:
        rain_clip = rain_clip.loop(duration=base_clip.duration)
    else:
        rain_clip = rain_clip.subclipped(0, base_clip.duration)

    rain_clip = rain_clip.resized(new_size=base_clip.size)
    opacity = 0.8

    def screen_blend_frames(get_frame, t):
        base_frame = get_frame(t).astype(np.float32) / 255.0
        rain_frame = rain_clip.get_frame(t).astype(np.float32) / 255.0
        
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
        else:
            rain_frame = rain_frame * opacity

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
    print(f"Saved Video: {output_video_path}")

def overlay_rain():
    RAIN_POOL_DIR = r"C:\Project_Works\MuyProjects\video_gen_toolkits\input\video_pools"
    INPUT_DIR = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\second_processed"
    OUTPUT_DIR = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\final_processed"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    video_exts = ('.mp4', '.avi', '.mov', '.mkv')
    image_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    supported_exts = video_exts + image_exts
    
    input_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(supported_exts)]

    if not input_files:
        print(f"No source videos or images found in {INPUT_DIR}")
        return

    # 1. Choose Processing Mode & resolve targets
    proc_mode, targets = select_processing_mode(input_files)
    
    # 2. Select rain video asset
    rain_video_path = select_rain_video_terminal(RAIN_POOL_DIR)

    def dispatch_processing(filename):
        source_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, f"enhanced_{filename}")
        
        if filename.lower().endswith(image_exts):
            process_image(source_path, output_path, rain_video_path)
        else:
            process_video(source_path, output_path, rain_video_path)

    # 3. Execution Engine
    if proc_mode == '1':
        # Single File Mode (targets contains exactly 1 user-chosen file)
        dispatch_processing(targets[0])
    else:
        # Batch Mode (targets contains all discovered files)
        print(f"\n--- Starting Batch Process ({len(targets)} files found) ---")
        for index, filename in enumerate(targets, start=1):
            print(f"\n[{index}/{len(targets)}]")
            dispatch_processing(filename)
            
        print("\n--- Batch Processing Complete! ---")

if __name__ == "__main__":
    overlay_rain()