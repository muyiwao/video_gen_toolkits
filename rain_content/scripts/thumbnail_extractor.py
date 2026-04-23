import cv2
import numpy as np
from pathlib import Path

# --- PATH CONFIGURATION ---
VIDEO_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced')
THUMB_OUT_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_long')
THUMB_OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- 4K & SIZE CONFIGURATION ---
TARGET_WIDTH = 3840  
MAX_FILE_SIZE_MB = 48 
MAX_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# --- RAIN INTENSITY CONFIGURATION ---
RAIN_TYPES = {
    "1": {"name": "Heavy Rain", "thresh": 8, "glow": 0.8, "offset": 30, "blur": 5},
    "2": {"name": "Soft Drizzle", "thresh": 18, "glow": 0.3, "offset": 10, "blur": 3},
    "3": {"name": "Rain Thunderstorm", "thresh": 6, "glow": 1.1, "offset": 45, "blur": 7},
    "4": {"name": "Windy Rain", "thresh": 10, "glow": 0.7, "offset": 25, "blur": 9}
}

def apply_universal_rain_logic(image, hero_diff_mask, rain_config):
    """
    Produces a 4K output with intensity-adjusted rain highlights.
    """
    h, w = image.shape[:2]
    aspect_ratio = w / h
    target_height = int(TARGET_WIDTH / aspect_ratio)
    
    # 1. High-Quality 4K Upscale
    image_4k = cv2.resize(image, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LANCZOS4)
    rain_mask = cv2.resize(hero_diff_mask, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LINEAR)
    
    # 2. Dynamic Mask Refinement based on Rain Type
    # Lower threshold = more rain detected; higher blur = thicker streaks
    rain_mask = cv2.GaussianBlur(rain_mask, (rain_config['blur'], rain_config['blur']), 0)
    _, rain_mask = cv2.threshold(rain_mask, rain_config['thresh'], 255, cv2.THRESH_BINARY)
    
    # 3. Intensity-Adjusted Highlight
    # We use the 'glow' and 'offset' to make rain pop without hitting global contrast
    rain_overlay = cv2.addWeighted(image_4k, 1.0, image_4k, rain_config['glow'], rain_config['offset']) 
    
    # Soften blending for 4K
    soft_mask = cv2.GaussianBlur(rain_mask, (7, 7), 0).astype(np.float32) / 255.0
    
    # 4. Merge
    final_4k = (image_4k * (1 - soft_mask[:,:,np.newaxis]) + 
                rain_overlay * soft_mask[:,:,np.newaxis]).astype(np.uint8)

    return final_4k

def get_hero_frame_with_mask(video_path):
    cap = cv2.VideoCapture(str(video_path))
    max_score, best_frame, best_mask = -1, None, None
    
    ret, f1 = cap.read()
    if not ret: return None, None
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)

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
    quality = 100
    success = False
    while quality > 50:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        result, encimg = cv2.imencode('.jpg', image, encode_param)
        if len(encimg) <= MAX_SIZE_BYTES:
            with open(out_path, "wb") as f:
                f.write(encimg)
            print(f"✅ Saved: {out_path.name} ({len(encimg)/(1024*1024):.2f} MB)")
            success = True
            break
        quality -= 2 
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

def generate_4k_rain_thumbs():
    # --- Video Selection ---
    video_files = sorted(list(VIDEO_DIR.glob("*.mp4")))
    if not video_files: return
    print("\n--- 4K Rain Thumbnail Engine ---")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file.name}")
    
    v_choice = input(f"\nSelect Video (1-{len(video_files)}): ")
    try:
        target_video = video_files[int(v_choice)-1]
    except: return

    # --- Rain Type Selection ---
    print("\n--- Select Rain Intensity Mode ---")
    for k, v in RAIN_TYPES.items():
        print(f"{k}. {v['name']}")
    
    t_choice = input("\nChoice: ")
    rain_config = RAIN_TYPES.get(t_choice, RAIN_TYPES["1"])

    print(f"\n🔍 Processing {target_video.name} as '{rain_config['name']}'...")
    
    raw, mask = get_hero_frame_with_mask(target_video)
    if raw is not None:
        raw_cropped = crop_16_9(raw)
        mask_cropped = crop_16_9(mask)
        
        enhanced_4k = apply_universal_rain_logic(raw_cropped, mask_cropped, rain_config)
        
        out_name = f"4K_{rain_config['name'].replace(' ', '_').upper()}_{target_video.stem}.jpg"
        save_with_size_constraint(enhanced_4k, THUMB_OUT_DIR / out_name)

if __name__ == "__main__":
    generate_4k_rain_thumbs()