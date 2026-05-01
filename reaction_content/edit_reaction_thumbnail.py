import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

def batch_process_thumbnails(input_folder, output_folder, target_size_mb=1.9):
    """
    Scans the input folder and processes every image into a 4K CTR-optimized thumbnail.
    """
    # Create output directory if it doesn't exist
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    
    # Grab all image files
    images = [f for f in input_path.iterdir() if f.suffix.lower() in valid_extensions]
    
    if not images:
        print(f"📂 No images found in {input_folder}")
        return

    print(f"🚀 Found {len(images)} images. Starting batch process...")

    for img_file in images:
        try:
            with Image.open(img_file) as img:
                # 1. 4K UPSCALE
                img_4k = img.resize((3840, 2160), resample=Image.Resampling.LANCZOS)

                # 2. COMMENTARY ENHANCEMENTS (Based on image_2.png style)
                img_4k = ImageEnhance.Contrast(img_4k).enhance(1.25)
                img_4k = ImageEnhance.Color(img_4k).enhance(1.4)
                img_4k = ImageEnhance.Sharpness(img_4k).enhance(1.5)
                img_4k = img_4k.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))

                # 3. SAVE & OPTIMIZE SIZE
                save_filename = f"4K_{img_file.stem}.jpg"
                final_destination = output_path / save_filename
                
                quality = 95
                limit = target_size_mb * 1024 * 1024
                
                # Use subsampling=0 for text/facial clarity
                img_4k.save(final_destination, "JPEG", quality=quality, optimize=True, subsampling=0)
                
                while os.path.getsize(final_destination) > limit and quality > 25:
                    quality -= 2
                    img_4k.save(final_destination, "JPEG", quality=quality, optimize=True, subsampling=0)

                print(f"✅ Processed: {img_file.name} -> {save_filename} ({quality}%)")

        except Exception as e:
            print(f"❌ Failed to process {img_file.name}: {e}")

    print(f"\n✨ Batch complete! Check your output folder: {output_folder}")

if __name__ == "__main__":
    # Configure your paths here
    SOURCE_PATH = "reaction_content/input_thumbs" 
    DESTINATION_PATH = "reaction_content/output_4k_thumbs"
    
    batch_process_thumbnails(SOURCE_PATH, DESTINATION_PATH)

