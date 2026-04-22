import cv2
import numpy as np
import os
from pathlib import Path

# --- 1. Path Configuration ---
RAW_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw')
OUTPUT_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def transform_frame(frame, mode):
    """
    Handles resizing and optional visual enhancement.
    mode 1: Full Enhancement (Upscale + Contrast + Sharpness)
    mode 2: Upscale Only
    """
    # 2x Upscale (Lanczos4 for best quality)
    width, height = int(frame.shape[1] * 2), int(frame.shape[0] * 2)
    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
    
    if mode == '1':
        # Contrast & Brightness
        frame = cv2.convertScaleAbs(frame, alpha=1.4, beta=15)
        
        # Advanced Sharpening (Unsharp Mask technique)
        gaussian_blur = cv2.GaussianBlur(frame, (0, 0), 3)
        frame = cv2.addWeighted(frame, 2.0, gaussian_blur, -1.0, 0)
    
    return frame

def save_image_with_limit(image, output_path, max_mb=19):
    """
    Saves image as PNG. If file exceeds max_mb, increases compression.
    If still too large, converts to high-quality JPEG.
    """
    max_bytes = max_mb * 1024 * 1024
    compression = 3 # Start with standard PNG compression
    
    # Initial Save
    cv2.imwrite(str(output_path), image, [cv2.IMWRITE_PNG_COMPRESSION, compression])
    
    # Check size and adjust
    if os.path.getsize(output_path) > max_bytes:
        print(f"⚠️ Initial save exceeded {max_mb}MB. Adjusting compression...")
        # Maximum PNG compression
        cv2.imwrite(str(output_path), image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        
    # Final check: If still too large, switch to JPEG
    if os.path.getsize(output_path) > max_bytes:
        print(f"⚠️ Still too large for PNG. Converting to high-quality JPEG...")
        output_path = output_path.with_suffix('.jpg')
        cv2.imwrite(str(output_path), image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
    return output_path

def process_image(file_path, mode):
    print(f"📸 Processing Image: {file_path.name}...")
    frame = cv2.imread(str(file_path))
    if frame is None:
        print(f"❌ Error: Could not read image {file_path.name}.")
        return

    transformed = transform_frame(frame, mode)
    output_path = OUTPUT_DIR / f"processed_{file_path.stem}.png"
    
    final_path = save_image_with_limit(transformed, output_path)
    print(f"✅ Success! Saved to: {final_path.name} ({os.path.getsize(final_path)/1024/1024:.2f} MB)")

def process_video(file_path, mode):
    print(f"🎬 Processing Video: {file_path.name}...")
    cap = cv2.VideoCapture(str(file_path))
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open video {file_path.name}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    output_path = OUTPUT_DIR / f"processed_{file_path.name}"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (orig_w*2, orig_h*2))

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        transformed = transform_frame(frame, mode)
        out.write(transformed)
        
        count += 1
        if count % 30 == 0:
            progress = int((count/total_frames)*100) if total_frames > 0 else 0
            print(f"   Processing: {progress}% complete...", end="\r")
        
    cap.release()
    out.release()
    print(f"\n✅ Success! Saved to: {output_path.name}")

def get_files_by_ext(directory, extensions):
    found_files = []
    for ext in extensions:
        found_files.extend(list(directory.glob(f"*{ext.lower()}")))
        found_files.extend(list(directory.glob(f"*{ext.upper()}")))
    return sorted(list(set(found_files)))

def main():
    print("\n--- Universal Rain Content Enhancer & Upscaler ---")
    
    # 1. Select Processing Mode
    print("\nSelect Mode:")
    print("1. Full Enhancement (Upscale + Contrast + Sharpen)")
    print("2. Upscale Only (Lanczos4 2x)")
    mode_choice = input("Selection (1-2): ").strip()

    # 2. Select File Type
    print("\nSelect Input Type:")
    print("1. Images (.jpg, .png, .webp)")
    print("2. Videos (.mp4, .mkv, .mov)")
    type_choice = input("Selection (1-2): ").strip()
    
    if type_choice == '1':
        files = get_files_by_ext(RAW_DIR, ['.png', '.jpg', '.jpeg', '.webp'])
    elif type_choice == '2':
        files = get_files_by_ext(RAW_DIR, ['.mp4', '.mkv', '.mov'])
    else:
        print("Invalid selection.")
        return

    if not files:
        print(f"No matching files found in {RAW_DIR}")
        return

    print(f"\nFound {len(files)} file(s).")
    process_all = input("Process ALL files in folder? (y/n): ").lower().strip()

    if process_all == 'y':
        for f in files:
            if type_choice == '1': process_image(f, mode_choice)
            else: process_video(f, mode_choice)
    else:
        for i, f in enumerate(files, 1):
            print(f"{i}. {f.name}")
        
        try:
            file_idx = int(input(f"Select file number (1-{len(files)}): "))
            target_file = files[file_idx - 1]
            if type_choice == '1': process_image(target_file, mode_choice)
            else: process_video(target_file, mode_choice)
        except (ValueError, IndexError):
            print("Invalid file selection.")

if __name__ == "__main__":
    main()