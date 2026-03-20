import cv2
import numpy as np
import os

# --- PATH CONFIGURATION ---
RAW_IMG_DIR = r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\raw'
OUTPUT_IMG_DIR = r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\rain_content\recorded\enhanced'

if not os.path.exists(OUTPUT_IMG_DIR):
    os.makedirs(OUTPUT_IMG_DIR)

def apply_soft_night_logic(image):
    """
    Optimized for Night scenes without the 'too sharp' or 'too much contrast' issues.
    Mimics the smoothness of the Day mode but keeps the Night atmosphere.
    """
    # 1. 2x Upscale (Standard)
    h, w = image.shape[:2]
    image = cv2.resize(image, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
    rows, cols = image.shape[:2]

    # 2. Softened Local Contrast (CLAHE)
    # Reduced clipLimit from 4.5 down to 2.2 to prevent 'crunchy' noise
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(10, 10)) # Larger grid = smoother transitions
    l = clahe.apply(l)
    image = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    # 3. Muted Global Exposure
    # alpha=1.1 (Slight boost) instead of 1.4+ 
    # beta=5 (Subtle lift) to prevent crushed blacks
    image = cv2.convertScaleAbs(image, alpha=1.1, beta=5)

    # 4. Cozy Warmth (LAB b-channel)
    # Keeping the yellow shift for that 'street lamp' glow
    lab_f = image.astype("float32")
    lab_f[:, :, 2] += 8 
    image = np.clip(lab_f, 0, 255).astype("uint8")

    # 5. Smooth Vignette
    # Uses a wider Gaussian spread to make the edges fade gradually
    is_vertical = rows > cols
    sigma_factor = 1.4 if is_vertical else 2.0
    kernel_x = cv2.getGaussianKernel(cols, cols / sigma_factor)
    kernel_y = cv2.getGaussianKernel(rows, rows / sigma_factor)
    mask = (kernel_y * kernel_x.T)
    mask = mask / mask.max()
    
    # Blend the vignette so it isn't a hard black circle
    mask = cv2.addWeighted(mask, 0.75, np.ones_like(mask), 0.25, 0)
    image = (image * mask[:, :, np.newaxis]).astype("uint8")

    # 6. Gentle Sharpening (The 'Video Script' Mirror)
    # Reduced weights to prevent 'ringing' artifacts or haloing around droplets
    gaussian_blur = cv2.GaussianBlur(image, (0, 0), 2)
    image = cv2.addWeighted(image, 1.4, gaussian_blur, -0.4, 0)

    return image

def process_thumbnails():
    extensions = ('.jpg', '.jpeg', '.png', '.webp')
    files = [f for f in os.listdir(RAW_IMG_DIR) if f.lower().endswith(extensions)]
    
    if not files:
        print("No images found!")
        return

    print(f"🚀 Processing {len(files)} thumbnails with SOFT NIGHT logic...")

    for filename in files:
        img = cv2.imread(os.path.join(RAW_IMG_DIR, filename))
        if img is None: continue
        
        result = apply_soft_night_logic(img)
        
        out_name = f"SOFT_NIGHT_{os.path.splitext(filename)[0]}.jpg"
        out_path = os.path.join(OUTPUT_IMG_DIR, out_name)
        cv2.imwrite(out_path, result, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"✅ Created: {out_name}")

if __name__ == "__main__":
    process_thumbnails()