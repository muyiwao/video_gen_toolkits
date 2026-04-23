import cv2
import numpy as np
from pathlib import Path

# --- PATH CONFIGURATION ---
VIDEO_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced')
THUMB_OUT_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_long')
THUMB_OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- 4K & SIZE CONFIGURATION ---
TARGET_WIDTH = 3840  # 4K UHD Width
MAX_FILE_SIZE_MB = 48 # Safe buffer under 49MB
MAX_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def apply_universal_rain_logic(image, hero_diff_mask):
    """
    Produces a 4K output while enhancing rain streaks via motion masking.
    """
    # 1. Precise 4K Upscale
    # We use INTER_LANCZOS4 for the highest quality resample possible
    h, w = image.shape[:2]
    aspect_ratio = w / h
    target_height = int(TARGET_WIDTH / aspect_ratio)
    
    image_4k = cv2.resize(image, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LANCZOS4)
    
    # Resize the motion mask to match 4K
    rain_mask = cv2.resize(hero_diff_mask, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LINEAR)
    
    # 2. Refine Rain Mask for 4K Density
    # Increased kernel sizes slightly to account for higher pixel density in 4K
    rain_mask = cv2.GaussianBlur(rain_mask, (5, 5), 0)
    _, rain_mask = cv2.threshold(rain_mask, 12, 255, cv2.THRESH_BINARY)
    
    # 3. Non-Destructive Highlight
    # We lift the raindrops specifically so they are visible on high-res displays
    rain_overlay = cv2.addWeighted(image_4k, 1.0, image_4k, 0.6, 25) 
    
    # Soften the mask for seamless blending at 4K
    soft_mask = cv2.GaussianBlur(rain_mask, (7, 7), 0).astype(np.float32) / 255.0
    
    # Merge: Final 4K Image
    final_4k = (image_4k * (1 - soft_mask[:,:,np.newaxis]) + 
                rain_overlay * soft_mask[:,:,np.newaxis]).astype(np.uint8)

    return final_4k

def get_hero_frame_with_mask(video_path):
    cap = cv2.VideoCapture(str(video_path))
    max_score, best_frame, best_mask = -1, None, None
    
    ret, f1 = cap.read()
    if not ret: return None, None
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)

    # Scan 300 frames to ensure we find a high-motion "Hero" moment
    for i in range(300):
        ret, f2 = cap.read()
        if not ret: break
        
        if i % 2 == 0:
            g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
            diff = cv2.absdiff(g1, g2)
            score = np.sum(diff)
            
            if score > max_score:
                max_score = score
                best_frame = f2.copy()
                best_mask = diff
            g1 = g2
            
    cap.release()
    return best_frame, best_mask

def save_with_size_constraint(image, out_path):
    # Start at Quality 100 for 4K detail
    quality = 100
    success = False
    
    while quality > 50:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        result, encimg = cv2.imencode('.jpg', image, encode_param)
        
        current_size = len(encimg)
        if current_size <= MAX_SIZE_BYTES:
            with open(out_path, "wb") as f:
                f.write(encimg)
            print(f"✅ 4K Saved: {out_path.name} ({current_size/(1024*1024):.2f} MB @ Quality: {quality})")
            success = True
            break
        quality -= 2 # Slower decrement to stay as close to 49MB as possible
    return success

def crop_16_9(image):
    h, w = image.shape[:2]
    target = 16/9
    if abs((w/h) - target) < 0.01: return image
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
        print("❌ No videos found"); return []
    print("\n--- 4K Thumbnail Generator ---")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file.name}")
    print(f"{len(video_files) + 1}. Process ALL")
    
    choice = input(f"\nSelect (1-{len(video_files) + 1}): ")
    if choice == str(len(video_files) + 1): return video_files
    try: return [video_files[int(choice)-1]]
    except: return []

def generate_4k_rain_thumbs():
    selected_videos = select_video_file()
    for v in selected_videos:
        print(f"🔍 Analyzing 4K potential for: {v.name}...")
        raw, mask = get_hero_frame_with_mask(v)
        
        if raw is not None:
            # Crop to 16:9 first so upscale is perfectly proportioned
            raw_cropped = crop_16_9(raw)
            mask_cropped = crop_16_9(mask)
            
            # Process into 4K
            enhanced_4k = apply_universal_rain_logic(raw_cropped, mask_cropped)
            
            out_path = THUMB_OUT_DIR / f"4K_RAIN_{v.stem}.jpg"
            save_with_size_constraint(enhanced_4k, out_path)

if __name__ == "__main__":
    generate_4k_rain_thumbs()