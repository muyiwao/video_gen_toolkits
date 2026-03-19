import cv2
import numpy as np
import os

# --- PATH CONFIGURATION ---
RAW_IMG_DIR = r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw'
OUTPUT_IMG_DIR = r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced'

if not os.path.exists(OUTPUT_IMG_DIR):
    os.makedirs(OUTPUT_IMG_DIR)

def apply_universal_thumbnail_logic(image, mode='night'):
    # 1. Upscale (2x) using Lanczos for high-fidelity edges
    width, height = int(image.shape[1] * 2), int(image.shape[0] * 2)
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LANCZOS4)

    # 2. Set Parameters based on Mode
    if mode == 'day':
        # Day mode: Lower contrast to protect bright skies, subtle brightness
        clip_limit = 2.5
        brightness = 0
        contrast = 1.05
    else:
        # Night mode: High contrast for "pop," slight brightness boost for shadows
        clip_limit = 4.5
        brightness = 8
        contrast = 1.15

    # 3. Local Contrast (CLAHE) - Makes droplets 3D
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8,8))
    l = clahe.apply(l)
    image = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    # 4. Global Exposure & Contrast
    image = cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

    # 5. Targeted "Cozy" Warmth (LAB b-channel shift)
    lab_f = image.astype("float32")
    # Increase yellow/warmth (b channel)
    lab_f[:,:,2] += 12 
    image = np.clip(lab_f, 0, 255).astype("uint8")

    # 6. Rain Glimmer (Top-Hat Transform)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
    bloom = cv2.GaussianBlur(tophat, (9, 9), 0)
    image = cv2.addWeighted(image, 1.0, cv2.merge([bloom, bloom, bloom]), 0.6, 0)

    # 7. Vignette (Focus Puller)
    rows, cols = image.shape[:2]
    kernel_x = cv2.getGaussianKernel(cols, cols/1.8)
    kernel_y = cv2.getGaussianKernel(rows, rows/1.8)
    mask = (kernel_y * kernel_x.T)
    mask = mask / mask.max()
    image = (image * mask[:, :, np.newaxis]).astype("uint8")

    # 8. Final Sharpening
    gaussian_blur = cv2.GaussianBlur(image, (0, 0), 2)
    image = cv2.addWeighted(image, 2.0, gaussian_blur, -1.0, 0)

    return image

def process_thumbnails():
    # Runtime Prompt
    print("--- Rain Thumbnail Generator ---")
    choice = input("Is the source material [D]ay or [N]ight? ").strip().lower()
    mode = 'day' if choice == 'd' else 'night'

    extensions = ('.jpg', '.jpeg', '.png')
    files = [f for f in os.listdir(RAW_IMG_DIR) if f.lower().endswith(extensions)]
    
    if not files:
        print("No images found!")
        return

    print(f"🚀 Processing {len(files)} images in {mode.upper()} mode...")

    for filename in files:
        img = cv2.imread(os.path.join(RAW_IMG_DIR, filename))
        if img is None: continue
        
        result = apply_universal_thumbnail_logic(img, mode=mode)
        
        out_path = os.path.join(OUTPUT_IMG_DIR, f"FINAL_{mode.upper()}_{filename}")
        cv2.imwrite(out_path, result, [cv2.IMWRITE_JPEG_QUALITY, 100])
        print(f"✅ Created: {out_path}")

if __name__ == "__main__":
    process_thumbnails()