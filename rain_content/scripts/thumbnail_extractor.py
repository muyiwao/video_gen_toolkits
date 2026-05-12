import cv2
import numpy as np
import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

# --- PATH CONFIGURATION ---
VIDEO_DIR = Path(r'C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\enhanced')
THUMB_OUT_DIR = Path(r'C:\Project_Works\MuyProjects\video_gen_toolkits\output')
OVERLAY_PATH = Path(r'C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\attachments\shorts\live_thumbnail_overlay.png')
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

def apply_section_dimming(image, focus_section):
    """Dims unselected sections of the image by 50%."""
    h, w = image.shape[:2]
    section_w = w // 3
    
    left = (0, section_w)
    center = (section_w, section_w * 2)
    right = (section_w * 2, w)

    dim_slices = []
    if focus_section == "R": dim_slices = [left, center]
    elif focus_section == "C": dim_slices = [left, right]
    elif focus_section == "L": dim_slices = [center, right]

    for s in dim_slices:
        sub_section = image[:, s[0]:s[1]]
        black_rect = np.zeros(sub_section.shape, dtype=np.uint8)
        image[:, s[0]:s[1]] = cv2.addWeighted(sub_section, 0.5, black_rect, 0.5, 0)
    
    return image

def apply_transparent_overlay(base_image, overlay_path):
    """Overlays a transparent PNG onto the base image."""
    if not overlay_path.exists():
        print(f"⚠️ Overlay not found at {overlay_path}. Skipping.")
        return base_image
    
    overlay = cv2.imread(str(overlay_path), cv2.IMREAD_UNCHANGED)
    overlay = cv2.resize(overlay, (base_image.shape[1], base_image.shape[0]), interpolation=cv2.INTER_LANCZOS4)
    
    b, g, r, a = cv2.split(overlay)
    overlay_rgb = cv2.merge((b, g, r))
    alpha = a.astype(float) / 255.0
    alpha_3d = cv2.merge([alpha, alpha, alpha])
    
    blended = (base_image.astype(float) * (1 - alpha_3d) + overlay_rgb.astype(float) * alpha_3d).astype(np.uint8)
    return blended

def create_motion_blur_kernel(length, angle):
    kernel = np.zeros((length, length))
    center = length // 2
    kernel[:, center] = 1.0
    matrix = cv2.getRotationMatrix2D((center, center), angle - 90, 1.0)
    kernel = cv2.warpAffine(kernel, matrix, (length, length))
    return kernel / np.sum(kernel)

def apply_ctr_enhancements(cv2_image):
    color_coverted = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(color_coverted)
    pil_img = ImageEnhance.Contrast(pil_img).enhance(1.25)
    pil_img = ImageEnhance.Color(pil_img).enhance(1.4)
    pil_img = ImageEnhance.Sharpness(pil_img).enhance(1.5)
    pil_img = pil_img.filter(ImageFilter.UnsharpMask(radius=2, percent=100, threshold=3))
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def process_frame_logic(image, hero_diff_mask, rain_config=None, focus_section=None, add_overlay=False):
    h, w = image.shape[:2]
    aspect_ratio = w / h
    target_height = int(TARGET_WIDTH / aspect_ratio)
    image_4k = cv2.resize(image, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LANCZOS4)
    
    if rain_config:
        rain_mask = cv2.resize(hero_diff_mask, (TARGET_WIDTH, target_height), interpolation=cv2.INTER_LINEAR)
        _, rain_mask = cv2.threshold(rain_mask, rain_config['thresh'], 255, cv2.THRESH_BINARY)
        kernel = create_motion_blur_kernel(rain_config['length'], rain_config['angle'])
        rain_mask = cv2.filter2D(rain_mask, -1, kernel)
        rain_overlay = cv2.addWeighted(image_4k, 1.0, image_4k, rain_config['glow'], rain_config['offset']) 
        soft_mask = cv2.GaussianBlur(rain_mask, (3, 3), 0).astype(np.float32) / 255.0
        image_4k = (image_4k * (1 - soft_mask[:,:,np.newaxis]) + 
                    rain_overlay * soft_mask[:,:,np.newaxis]).astype(np.uint8)

    # 1. Enhance
    enhanced = apply_ctr_enhancements(image_4k)
    
    # 2. Dim Sections
    if focus_section and focus_section in ["L", "C", "R"]:
        enhanced = apply_section_dimming(enhanced, focus_section)
    
    # 3. Conditional Overlay
    if add_overlay:
        enhanced = apply_transparent_overlay(enhanced, OVERLAY_PATH)

    return enhanced

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
    sampling_factor = cv2.IMWRITE_JPEG_SAMPLING_FACTOR_444
    while quality > 40:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality, int(cv2.IMWRITE_JPEG_SAMPLING_FACTOR), sampling_factor]
        result, encimg = cv2.imencode('.jpg', image, encode_param)
        if len(encimg) <= MAX_SIZE_BYTES:
            with open(out_path, "wb") as f: f.write(encimg)
            print(f"✅ Saved: {out_path.name} ({len(encimg)/(1024*1024):.2f} MB) @ {quality}% quality")
            return True
        quality -= 2 
    return False

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
    if not video_files: return

    print("\n--- 4K Rain Engine ---")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file.name}")
    
    try:
        v_choice = input(f"\nSelect Video: ")
        target_video = video_files[int(v_choice)-1]
    except: return

    # Runtime Overlay Choice
    o_choice = input("Add Live Thumbnail Overlay? (y/n) [n]: ").strip().lower()
    add_overlay = True if o_choice == 'y' else False

    print("\nSelect Focus Section: L: Left | C: Center | R: Right | N: None")
    f_choice = input("Choice: ").strip().upper()

    print("\nSelect Rain Intensity:")
    for k, v in RAIN_TYPES.items(): print(f"{k}. {v['name']}")
    t_choice = input("Choice [0 for Raw]: ").strip()
    rain_config = RAIN_TYPES.get(t_choice, None)

    raw, mask = get_hero_frame_with_mask(target_video)
    if raw is not None:
        raw_c, mask_c = crop_16_9(raw), crop_16_9(mask)
        final_thumb = process_frame_logic(raw_c, mask_c, rain_config, f_choice, add_overlay)
        
        label = rain_config['name'].replace(' ', '_').upper() if rain_config else "RAW"
        out_name = f"THUMB_4K_{label}_{target_video.stem}.jpg"
        save_with_size_constraint(final_thumb, THUMB_OUT_DIR / out_name)

if __name__ == "__main__":
    generate_4k_rain_thumbs()