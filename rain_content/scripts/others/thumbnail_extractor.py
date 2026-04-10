import cv2
import numpy as np
import os
from pathlib import Path

# --- PATH CONFIGURATION ---
VIDEO_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced')
THUMB_OUT_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_long')
THUMB_OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- SIZE LIMIT CONFIGURATION ---
MAX_FILE_SIZE_MB = 45  # Set slightly lower than 49MB for safety buffer
MAX_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def apply_universal_rain_logic(image):
    """
    Universal logic that adapts to both indoor and outdoor scenes.
    """
    # 1. High-Quality 2x Upscale
    h, w = image.shape[:2]
    image = cv2.resize(image, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
    
    # 2. Environmental Isolation
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth_base = cv2.medianBlur(gray, 15) 
    rain_detail_mask = cv2.absdiff(gray, smooth_base)
    _, rain_detail_mask = cv2.threshold(rain_detail_mask, 15, 255, cv2.THRESH_BINARY)
    
    # 3. Subject Protection
    subject_protection = cv2.inRange(gray, 40, 180) 
    final_mask = cv2.bitwise_and(rain_detail_mask, cv2.bitwise_not(subject_protection))
    final_mask = cv2.GaussianBlur(final_mask, (5, 5), 0).astype(np.float32) / 255.0

    # 4. Apply Rain Sparkle
    sparkle_layer = cv2.convertScaleAbs(image, alpha=1.4, beta=10)
    image = (image * (1 - final_mask[:,:,np.newaxis]) + 
             sparkle_layer * final_mask[:,:,np.newaxis]).astype(np.uint8)

    # 5. Adaptive Contrast (CLAHE)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    image = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    # 6. Cinematic Depth (Vignette)
    rows, cols = image.shape[:2]
    kernel_x = cv2.getGaussianKernel(cols, cols / 1.8)
    kernel_y = cv2.getGaussianKernel(rows, rows / 1.8)
    vignette = (kernel_y * kernel_x.T)
    vignette = vignette / vignette.max()
    vignette = cv2.addWeighted(vignette, 0.85, np.ones_like(vignette), 0.15, 0)
    image = (image * vignette[:, :, np.newaxis]).astype("uint8")

    return image

def save_with_size_constraint(image, out_path):
    """
    Saves the image as a JPEG, reducing quality iteratively if the size limit is exceeded.
    """
    quality = 95  # Start at high quality
    success = False
    
    while quality > 30:
        # Encode image to memory first to check size without excessive disk I/O
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        result, encimg = cv2.imencode('.jpg', image, encode_param)
        
        file_size = len(encimg)
        
        if file_size <= MAX_SIZE_BYTES:
            with open(out_path, "wb") as f:
                f.write(encimg)
            print(f"✅ Saved: {out_path.name} ({file_size / (1024*1024):.2f} MB at Quality: {quality})")
            success = True
            break
        
        quality -= 5  # Reduce quality and try again
        
    if not success:
        print(f"⚠️ Could not meet size constraint for {out_path.name} even at low quality.")

def get_hero_frame(video_path):
    cap = cv2.VideoCapture(str(video_path))
    max_score, best_frame = -1, None
    ret, f1 = cap.read()
    if not ret: return None
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)

    for i in range(180):
        ret, f2 = cap.read()
        if not ret: break
        if i % 4 == 0:
            g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
            edges = cv2.Sobel(cv2.absdiff(g1, g2), cv2.CV_64F, 1, 1, ksize=3)
            score = np.sum(np.absolute(edges))
            if score > max_score:
                max_score, best_frame = score, f2.copy()
            g1 = g2
    cap.release()
    return best_frame

def crop_16_9(image):
    h, w = image.shape[:2]
    target = 16/9
    if w/h > target:
        nw = int(h * target)
        s = (w - nw) // 2
        return image[:, s:s+nw]
    nh = int(w / target)
    s = (h - nh) // 2
    return image[s:s+nh, :]

def select_video_file():
    video_files = sorted(list(VIDEO_DIR.glob("*.mp4")))
    if not video_files:
        print(f"❌ No MP4 files found in {VIDEO_DIR}")
        return []

    print("\n--- Available Videos ---")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file.name}")
    print(f"{len(video_files) + 1}. Process ALL files")
    
    try:
        choice = int(input(f"\nSelect (1-{len(video_files) + 1}): "))
        if choice == len(video_files) + 1:
            return video_files
        elif 1 <= choice <= len(video_files):
            return [video_files[choice - 1]]
        return []
    except ValueError:
        return []

def generate_universal_thumbs():
    selected_videos = select_video_file()
    if not selected_videos: return

    for v in selected_videos:
        print(f"🔍 Analyzing: {v.name}...")
        raw = get_hero_frame(v)
        if raw is not None:
            enhanced = apply_universal_rain_logic(crop_16_9(raw))
            out_path = THUMB_OUT_DIR / f"MASTER_THUMB_{v.stem}.jpg"
            save_with_size_constraint(enhanced, out_path)
        else:
            print(f"❌ Could not read frames from {v.name}")

if __name__ == "__main__":
    generate_universal_thumbs()