import cv2
import numpy as np
import os

# 1. Use absolute paths to eliminate "Current Working Directory" confusion
RAW_DIR = r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw'
OUTPUT_DIR = r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def enhance_frame(frame):
    # Upscale
    width, height = int(frame.shape[1] * 2), int(frame.shape[0] * 2)
    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
    # Contrast & Sharpness
    frame = cv2.convertScaleAbs(frame, alpha=1.4, beta=15)
    gaussian_blur = cv2.GaussianBlur(frame, (0, 0), 3)
    frame = cv2.addWeighted(frame, 2.0, gaussian_blur, -1.0, 0)
    return frame

def process_raw_video(filename):
    # Verify file existence before even trying OpenCV
    input_path = os.path.join(RAW_DIR, filename)
    
    if not os.path.exists(input_path):
        print(f"❌ ERROR: File does not exist at {input_path}")
        print(f"Available files in raw folder: {os.listdir(RAW_DIR)}")
        return

    output_path = os.path.join(OUTPUT_DIR, f"enhanced_{filename}")
    cap = cv2.VideoCapture(input_path)

    # Check if OpenCV backend can actually read the file
    if not cap.isOpened():
        print(f"❌ ERROR: OpenCV could not open the video container for {filename}.")
        print("Try renaming the file to .mkv or checking if your environment has opencv-python-headless vs opencv-python.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Use 'mp4v' or 'avc1' for better compatibility
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (orig_w*2, orig_h*2))

    print(f"🚀 Processing: {filename}...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        enhanced = enhance_frame(frame)
        out.write(enhanced)
        
    cap.release()
    out.release()
    print(f"✅ Success! Saved to: {output_path}")

if __name__ == "__main__":
    # Diagnostic: Print the path being searched
    print(f"Searching for videos in: {RAW_DIR}")
    
    # Auto-detect the first mp4 if you aren't sure of the exact name
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".mp4")]
    if files:
        process_raw_video(files[0])
    else:
        print("No .mp4 files found in the raw directory.")