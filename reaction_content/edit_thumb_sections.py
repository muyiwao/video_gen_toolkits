import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

def batch_process_thumbnails(input_folder, output_folder, target_size_mb=1.9):
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
                # 1. 4K UPSCALE (Base)
                img_4k = img.resize((3840, 2160), resample=Image.Resampling.LANCZOS)
                width, height = img_4k.size

                # 2. DEFINE REGIONS
                split_x = int(width * 0.66) 
                
                # Create boxes
                left_center_box = (0, 0, split_x, height)
                right_box = (split_x, 0, width, height)

                # Crop sections
                full_enhanced_left = img_4k.crop(left_center_box)
                original_right = img_4k.crop(right_box)

                # Helper to apply the enhancement suite
                def apply_suite(image_part):
                    temp = ImageEnhance.Contrast(image_part).enhance(1.25)
                    temp = ImageEnhance.Color(temp).enhance(1.4)
                    temp = ImageEnhance.Sharpness(temp).enhance(1.5)
                    return temp.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))

                # 3. APPLY SELECTIVE LOGIC
                # Left/Center gets 100% enhancement
                final_left = apply_suite(full_enhanced_left)

                # Right gets 50% enhancement (Blend Original with Fully Enhanced version)
                full_enhanced_right = apply_suite(original_right)
                final_right = Image.blend(original_right, full_enhanced_right, 0.5)

                # 4. REASSEMBLE
                img_4k.paste(final_left, (0, 0))
                img_4k.paste(final_right, (split_x, 0))

                # 5. SAVE & OPTIMIZE
                save_filename = f"4K_Hybrid_{img_file.stem}.jpg"
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

    print(f"\n✨ Batch complete!")

if __name__ == "__main__":
    SOURCE_PATH = "reaction_content/input_thumbs" 
    DESTINATION_PATH = "reaction_content/output_4k_thumbs"
    batch_process_thumbnails(SOURCE_PATH, DESTINATION_PATH)