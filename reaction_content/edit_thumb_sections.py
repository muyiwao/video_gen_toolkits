import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

def batch_process_thumbnails(input_folder, output_folder, target_size_mb=1.9):
    """
    Scans the input folder and processes every image into a 4K CTR-optimized thumbnail.
    Enhancements are applied only to the Left and Center portions (first 66%).
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    images = [f for f in input_path.iterdir() if f.suffix.lower() in valid_extensions]
    
    if not images:
        print(f"📂 No images found in {input_folder}")
        return

    print(f"🚀 Found {len(images)} images. Starting batch process...")

    for img_file in images:
        try:
            with Image.open(img_file) as img:
                # 1. 4K UPSCALE (This is our base)
                img_4k = img.resize((3840, 2160), resample=Image.Resampling.LANCZOS)
                width, height = img_4k.size

                # 2. SELECTIVE ENHANCEMENTS
                # Define the split point (e.g., 2/3 for Left + Center)
                split_x = int(width * 0.66) 
                
                # Crop the portion to be enhanced
                left_center_box = (0, 0, split_x, height)
                enhanced_part = img_4k.crop(left_center_box)

                # Apply enhancements to the cropped portion ONLY
                enhanced_part = ImageEnhance.Contrast(enhanced_part).enhance(1.25)
                enhanced_part = ImageEnhance.Color(enhanced_part).enhance(1.4)
                enhanced_part = ImageEnhance.Sharpness(enhanced_part).enhance(1.5)
                enhanced_part = enhanced_part.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))

                # Paste the enhanced portion back onto the original 4K base
                # The Right section (from split_x to width) remains untouched
                img_4k.paste(enhanced_part, (0, 0))

                # 3. SAVE & OPTIMIZE SIZE
                save_filename = f"4K_Selective_{img_file.stem}.jpg"
                final_destination = output_path / save_filename
                
                quality = 95
                limit = target_size_mb * 1024 * 1024
                
                img_4k.save(final_destination, "JPEG", quality=quality, optimize=True, subsampling=0)
                
                while os.path.getsize(final_destination) > limit and quality > 25:
                    quality -= 2
                    img_4k.save(final_destination, "JPEG", quality=quality, optimize=True, subsampling=0)

                print(f"✅ Processed: {img_file.name} -> {save_filename} ({quality}%)")

        except Exception as e:
            print(f"❌ Failed to process {img_file.name}: {e}")

    print(f"\n✨ Batch complete! Output: {output_folder}")

if __name__ == "__main__":
    SOURCE_PATH = "reaction_content/input_thumbs" 
    DESTINATION_PATH = "reaction_content/output_4k_thumbs"
    batch_process_thumbnails(SOURCE_PATH, DESTINATION_PATH)