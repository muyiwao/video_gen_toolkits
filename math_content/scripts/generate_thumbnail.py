import os
import re
from datetime import datetime
from textwrap import wrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
BASE_PATH = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits")
ASSET_DIR = BASE_PATH / "math_content" / "attachments" / "long"
TEMPLATE_FILENAME = "thumbnail-template.png"
OUTPUT_DIR = BASE_PATH / "output" / "output_long"

# Using Arial Bold for that heavy impact look
FONT_PATH = r"C:\Windows\Fonts\arialbd.ttf"

# Set a much larger starting font size for big impact
DEFAULT_FONT_SIZE = 500 
CAPTION_COLOR = (255, 255, 255) # White

def generate_thumbnail_with_caption():
    """
    Generates high-impact thumbnails with massive, bold centered text.
    """
    print("\n--- Youtube Massive Bold Caption Generator ---")
    
    template_path = ASSET_DIR / TEMPLATE_FILENAME
    if not template_path.exists():
        print(f"❌ Template file not found at {template_path}")
        return

    while True:
        raw_caption = input("\n💬 Enter caption (or Enter to exit): ").strip()
        if not raw_caption:
            break

        safe_base_name = re.sub(r'[\\/*?:"<>|]', '', raw_caption).replace(' ', '_')[:25]
        output_filename = OUTPUT_DIR / f"thumb_{safe_base_name}_{datetime.now().strftime('%H%M%S')}.png"

        try:
            with Image.open(template_path) as template_img:
                draw = ImageDraw.Draw(template_img)
                w_img, h_img = template_img.size
                
                # --- IMPACT OPTIMIZATION ---
                # We want the text to occupy 90% of the width and 80% of the height
                max_w_const = int(w_img * 0.9)
                max_h_const = int(h_img * 0.8)
                
                current_font_size = DEFAULT_FONT_SIZE
                
                # We reduce the wrap width to 12-15 characters to force 
                # the "Stacked" look seen in your example.
                wrapped_text = "\n".join(wrap(raw_caption.upper(), width=15))

                # DYNAMIC SIZING
                while current_font_size > 50:
                    try:
                        font = ImageFont.truetype(FONT_PATH, current_font_size)
                    except IOError:
                        print("❌ Font not found. Check FONT_PATH.")
                        return

                    # Calculate size
                    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center', spacing=20)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]

                    if text_w <= max_w_const and text_h <= max_h_const:
                        break
                    current_font_size -= 10

                # CENTER CALCULATION
                x_pos = (w_img - text_w) // 2
                y_pos = (h_img - text_h) // 2

                # DRAW WITH HEAVY SPACING
                draw.multiline_text(
                    (x_pos, y_pos),
                    wrapped_text,
                    font=font,
                    fill=CAPTION_COLOR,
                    align='center',
                    spacing=25 # Increased spacing for better readability
                )

                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                template_img.save(output_filename)
                print(f"✅ Created: {output_filename.name} (Font Size: {current_font_size})")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_thumbnail_with_caption()