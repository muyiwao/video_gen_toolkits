import cv2
import numpy as np
import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

# --- PATH CONFIGURATION ---
VIDEO_DIR = Path(r'C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\enhanced')
THUMB_OUT_DIR = Path(r'C:\Project_Works\MuyProjects\video_gen_toolkits\output\output_long')
THUMB_OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_WIDTH = 3840  
MAX_SIZE_BYTES = 1.9 * 1024 * 1024

# --- RAIN INTENSITY CONFIGURATION ---
RAIN_TYPES = {
    "1": {"name": "Heavy Rain", "thresh": 12, "glow": 0.6, "offset": 20, "length": 45, "angle": 85},
    "2": {"name": "Soft Drizzle", "thresh": 22, "glow": 0.2, "offset": 10, "length": 20, "angle": 90},
    "3": {"name": "Rain Thunderstorm", "thresh": 10, "glow": 0.9, "offset": 40, "length": 65, "angle": 80},
    "4": {"name": "Windy Rain", "thresh": 15, "glow": 0.5, "offset": 25, "length": 80, "angle": 45}
}

def create_motion_blur_kernel(length, angle):
    """Creates a kernel for directional motion blur to simulate rain streaks."""
    kernel = np.zeros((length, length))
    center = length // 2
    kernel[:, center] = 1.0
    
    # Rotate the kernel to the desired angle
    matrix = cv2.getRotationMatrix2D((center, center), angle - 90, 1.0)
    kernel = cv2.warpAffine(kernel, matrix, (length, length))
    
    return kernel / np.sum(kernel)

def apply_ctr_enhancements(cv2_image):
    """Applies high-contrast and vibrancy pops for SEO/CTR."""
    color_coverted = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(color_coverted)
    
    pil_img = ImageEnhance.Contrast(pil_img).enhance(1.25)
    pil_img = ImageEnhance.Color(pil_img).enhance(1.4)
    pil_img = ImageEnhance.Sharpness(pil_img).enhance(1.5)
    pil_img = pil_img.filter(ImageFilter.UnsharpMask(radius=2, percent=100, threshold=3))
    
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def process_frame_logic(image, hero_diff_mask, rain_config=None):
    """Handles upscaling, streak generation, and final color enhancement."""
    h, w = image.shape[:2]
    aspect_ratio = w / h
    target_height = int(TARGET_WIDTH / aspect_ratio)
    image_4k = cv2.resize(image, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LANCZOS4)
    
    if rain_config:
        # Resize and threshold mask
        rain_mask = cv2.resize(hero_diff_mask, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LINEAR)
        _, rain_mask = cv2.threshold(rain_mask, rain_config['thresh'], 255, cv2.THRESH_BINARY)
        
        # Convert dots to STREAKS using Motion Blur Kernel
        kernel = create_motion_blur_kernel(rain_config['length'], rain_config['angle'])
        rain_mask = cv2.filter2D(rain_mask, -1, kernel)
        
        # Create atmospheric glow layer
        rain_overlay = cv2.addWeighted(image_4k, 1.0, image_4k, rain_config['glow'], rain_config['offset']) 
        
        # Soften mask for natural blending
        soft_mask = cv2.GaussianBlur(rain_mask, (3, 3), 0).astype(np.float32) / 255.0
        
        image_4k = (image_4k * (1 - soft_mask[:,:,np.newaxis]) + 
                    rain_overlay * soft_mask[:,:,np.newaxis]).astype(np.uint8)

    return apply_ctr_enhancements(image_4k)

def get_hero_frame_with_mask(video_path):
    """Analyzes first 300 frames to find the frame with the most motion (rain particles)."""
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
    """Saves as JPEG with 4:4:4 sampling and iterative quality reduction to fit file size."""
    quality = 95
    # Fix for Warning: Use explicit OpenCV enum for sampling
    sampling_factor = cv2.IMWRITE_JPEG_SAMPLING_FACTOR_444

    while quality > 40:
        encode_param = [
            int(cv2.IMWRITE_JPEG_QUALITY), quality,
            int(cv2.IMWRITE_JPEG_SAMPLING_FACTOR), sampling_factor
        ]
        result, encimg = cv2.imencode('.jpg', image, encode_param)
        
        if len(encimg) <= MAX_SIZE_BYTES:
            with open(out_path, "wb") as f:
                f.write(encimg)
            print(f"✅ Saved: {out_path.name} ({len(encimg)/(1024*1024):.2f} MB) @ {quality}% quality")
            return True
        quality -= 2 
    return False

def crop_16_9(image):
    """Ensures the frame is a perfect 16:9 aspect ratio before upscaling."""
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
    """Main execution flow for generating thumbnails."""
    video_files = sorted(list(VIDEO_DIR.glob("*.mp4")))
    if not video_files: 
        print(f"❌ No videos found in {VIDEO_DIR}")
        return

    print("\n--- 4K Rain Streak Engine ---")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file.name}")
    
    try:
        v_choice = input(f"\nSelect Video (1-{len(video_files)}): ")
        target_video = video_files[int(v_choice)-1]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return

    print("\n--- Select Rain Intensity Mode ---")
    print("0. Raw Enhance (No Streaks/Mask)")
    for k, v in RAIN_TYPES.items():
        print(f"{k}. {v['name']}")
    
    t_choice = input("\nChoice [Default 0]: ").strip()
    rain_config = RAIN_TYPES.get(t_choice, None)

    print(f"\n🔍 Analyzing video and applying streaks to {target_video.name}...")
    
    raw, mask = get_hero_frame_with_mask(target_video)
    
    if raw is not None:
        raw_c = crop_16_9(raw)
        mask_c = crop_16_9(mask)
        
        enhanced_4k = process_frame_logic(raw_c, mask_c, rain_config)
        
        label = rain_config['name'].replace(' ', '_').upper() if rain_config else "RAW_ENHANCE"
        out_name = f"STREAK_4K_{label}_{target_video.stem}.jpg"
        save_with_size_constraint(enhanced_4k, THUMB_OUT_DIR / out_name)
    else:
        print("❌ Failed to extract frame from video.")

if __name__ == "__main__":
    generate_4k_rain_thumbs()