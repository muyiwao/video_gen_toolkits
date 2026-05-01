import cv2
import numpy as np
import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

# --- PATH CONFIGURATION ---
VIDEO_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced')
THUMB_OUT_DIR = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\output\output_long')
THUMB_OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- CTR & PLATFORM CONFIGURATION ---
TARGET_WIDTH = 3840  
MAX_SIZE_BYTES = 1.9 * 1024 * 1024  # Strict YouTube 2MB Limit

# --- RAIN INTENSITY CONFIGURATION ---
RAIN_TYPES = {
    "1": {"name": "Heavy Rain", "thresh": 8, "glow": 0.8, "offset": 30, "blur": 5},
    "2": {"name": "Soft Drizzle", "thresh": 18, "glow": 0.3, "offset": 10, "blur": 3},
    "3": {"name": "Rain Thunderstorm", "thresh": 6, "glow": 1.1, "offset": 45, "blur": 7},
    "4": {"name": "Windy Rain", "thresh": 10, "glow": 0.7, "offset": 25, "blur": 9}
}

def apply_ctr_enhancements(cv2_image):
    """
    Applies the 'Rain SEO Master List' visual pops: 
    Vibrancy, Contrast, and Sharpness via PIL.
    """
    # Convert CV2 (BGR) to PIL (RGB)
    color_coverted = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(color_coverted)

    # 1. Boost Contrast (1.25x) - Makes rain highlights pop against dark backgrounds
    pil_img = ImageEnhance.Contrast(pil_img).enhance(1.25)
    
    # 2. Boost Saturation (1.4x) - Vital for 'Nature' and 'Atmospheric' CTR
    pil_img = ImageEnhance.Color(pil_img).enhance(1.4)
    
    # 3. Professional Sharpening - Emphasizes texture of rain and environment
    pil_img = ImageEnhance.Sharpness(pil_img).enhance(1.5)
    pil_img = pil_img.filter(ImageFilter.UnsharpMask(radius=2, percent=100, threshold=3))

    # Convert back to BGR for the CV2 saving logic
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def apply_universal_rain_logic(image, hero_diff_mask, rain_config):
    h, w = image.shape[:2]
    aspect_ratio = w / h
    target_height = int(TARGET_WIDTH / aspect_ratio)
    
    # 1. High-Quality 4K Upscale
    image_4k = cv2.resize(image, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LANCZOS4)
    rain_mask = cv2.resize(hero_diff_mask, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LINEAR)
    
    # 2. Dynamic Mask Refinement
    rain_mask = cv2.GaussianBlur(rain_mask, (rain_config['blur'], rain_config['blur']), 0)
    _, rain_mask = cv2.threshold(rain_mask, rain_config['thresh'], 255, cv2.THRESH_BINARY)
    
    # 3. Rain Highlight Layer
    rain_overlay = cv2.addWeighted(image_4k, 1.0, image_4k, rain_config['glow'], rain_config['offset']) 
    soft_mask = cv2.GaussianBlur(rain_mask, (7, 7), 0).astype(np.float32) / 255.0
    
    # 4. Merge Rain Logic
    final_4k = (image_4k * (1 - soft_mask[:,:,np.newaxis]) + 
                rain_overlay * soft_mask[:,:,np.newaxis]).astype(np.uint8)

    # 5. --- NEW: APPLY CTR POP ---
    return apply_ctr_enhancements(final_4k)

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
    quality = 95
    success = False
    while quality > 40:
        # Using [subsampling, 0] to maintain 4:4:4 chroma for maximum 'crispiness'
        # This prevents the red/blue hues in rain from blurring.
        encode_param = [
            int(cv2.IMWRITE_JPEG_QUALITY), quality,
            int(cv2.IMWRITE_JPEG_SAMPLING_FACTOR), 0
        ]
        result, encimg = cv2.imencode('.jpg', image, encode_param)
        
        if len(encimg) <= MAX_SIZE_BYTES:
            with open(out_path, "wb") as f:
                f.write(encimg)
            print(f"✅ Saved CTR-Optimized: {out_path.name} ({len(encimg)/(1024*1024):.2f} MB) at {quality}% Quality")
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
    video_files = sorted(list(VIDEO_DIR.glob("*.mp4")))
    if not video_files: 
        print(f"❌ No videos found in {VIDEO_DIR}")
        return

    print("\n--- 4K Rain CTR Thumbnail Engine ---")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file.name}")
    
    v_choice = input(f"\nSelect Video (1-{len(video_files)}): ")
    try:
        target_video = video_files[int(v_choice)-1]
    except: return

    print("\n--- Select Rain Intensity Mode ---")
    for k, v in RAIN_TYPES.items():
        print(f"{k}. {v['name']}")
    
    t_choice = input("\nChoice: ")
    rain_config = RAIN_TYPES.get(t_choice, RAIN_TYPES["1"])

    print(f"\n🔍 Processing {target_video.name}...")
    
    raw, mask = get_hero_frame_with_mask(target_video)
    if raw is not None:
        raw_cropped = crop_16_9(raw)
        mask_cropped = crop_16_9(mask)
        
        # Apply Rain Logic + CTR Pop
        enhanced_4k = apply_universal_rain_logic(raw_cropped, mask_cropped, rain_config)
        
        out_name = f"CTR_4K_{rain_config['name'].replace(' ', '_').upper()}_{target_video.stem}.jpg"
        save_with_size_constraint(enhanced_4k, THUMB_OUT_DIR / out_name)

if __name__ == "__main__":
    generate_4k_rain_thumbs()