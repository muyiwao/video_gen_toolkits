import cv2
import numpy as np
from pathlib import Path

# --- 1. Path Configuration ---
RAW_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw')
OUTPUT_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def enhance_frame(frame, mode):
    """
    Unified logic with mode switching:
    Mode 1: 2x Upscale + Contrast + Sharpness
    Mode 2: 2x Upscale ONLY
    """
    # High-Quality 2x Upscale (Common to both modes)
    width, height = int(frame.shape[1] * 2), int(frame.shape[0] * 2)
    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
    
    if mode == '1':
        # Contrast & Brightness
        frame = cv2.convertScaleAbs(frame, alpha=1.4, beta=15)
        
        # Advanced Sharpening (Unsharp Mask)
        gaussian_blur = cv2.GaussianBlur(frame, (0, 0), 3)
        frame = cv2.addWeighted(frame, 2.0, gaussian_blur, -1.0, 0)
        
    return frame

def process_image(file_path, mode):
    label = "Enhancing" if mode == '1' else "Upscaling"
    print(f"📸 {label} Image: {file_path.name}...")
    
    frame = cv2.imread(str(file_path))
    if frame is None:
        print(f"❌ Error: Could not read image {file_path.name}.")
        return

    enhanced = enhance_frame(frame, mode)
    
    prefix = "enhanced_" if mode == '1' else "upscaled_"
    output_path = OUTPUT_DIR / f"{prefix}{file_path.stem}.png"
    
    cv2.imwrite(str(output_path), enhanced, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    print(f"✅ Success! Saved to: {output_path.name}")

def process_video(file_path, mode):
    label = "Enhancing" if mode == '1' else "Upscaling"
    print(f"🎬 {label} Video: {file_path.name}...")
    
    cap = cv2.VideoCapture(str(file_path))
    if not cap.isOpened():
        print(f"❌ Error: Could not open video {file_path.name}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    prefix = "enhanced_" if mode == '1' else "upscaled_"
    output_path = OUTPUT_DIR / f"{prefix}{file_path.name}"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (orig_w*2, orig_h*2))

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        processed = enhance_frame(frame, mode)
        out.write(processed)
        
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
    print("\n--- Universal Rain Content Processor ---")
    
    # 1. Select Processing Mode
    print("\nSelect Processing Mode:")
    print("1. Full Enhancement (Upscale + Contrast + Sharp)")
    print("2. Simple Upscale (2x Resize Only)")
    mode = input("Selection (1-2) [Default 1]: ").strip() or '1'
    
    # 2. Select File Type
    print("\nSelect Input Type:")
    print("1. Images (.jpg, .png, .webp, .jpeg)")
    print("2. Videos (.mp4, .mkv, .mov)")
    choice = input("Selection (1-2): ").strip()
    
    if choice == '1':
        files = get_files_by_ext(RAW_DIR, ['.png', '.jpg', '.jpeg', '.webp'])
    elif choice == '2':
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
            if choice == '1': process_image(f, mode)
            else: process_video(f, mode)
    else:
        print("\nAvailable Files:")
        for i, f in enumerate(files, 1):
            print(f"{i}. {f.name}")
        
        try:
            file_idx = int(input(f"Select file number (1-{len(files)}): "))
            target_file = files[file_idx - 1]
            if choice == '1': process_image(target_file, mode)
            else: process_video(target_file, mode)
        except (ValueError, IndexError):
            print("Invalid file selection.")

if __name__ == "__main__":
    main()