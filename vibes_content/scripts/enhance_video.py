import subprocess
import os

def enhance_with_bg_and_logo(input_path, logo_path, output_dir):
    # Check if logo exists before running FFmpeg to prevent crash
    if not os.path.exists(logo_path):
        print(f"CRITICAL ERROR: Logo not found at {logo_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_name = "ultra_crispy_branded_vibes.mp4"
    output_path = os.path.join(output_dir, output_name)
    
    # Layer 1: Blurred Background
    # Layer 2: Sharpened Landscape Foreground
    # Layer 3: Logo Overlay
    filter_complex = (
        "[0:v]crop=iw:iw*9/16[crop_src];"
        "[crop_src]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg];"
        "[0:v]crop=iw:iw*9/16,scale=1080:-1:flags=lanczos,unsharp=5:5:1.2:5:5:0.0[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v_base];"
        "[v_base][1:v]overlay=W-w-50:50[v_final]"
    )
    
    cmd = [
        'ffmpeg', 
        '-i', input_path,
        '-i', logo_path,
        '-filter_complex', filter_complex,
        '-map', '[v_final]',
        '-map', '0:a?',
        '-c:v', 'libx264', 
        '-crf', '16', 
        '-preset', 'slow', 
        '-pix_fmt', 'yuv420p', 
        '-y', output_path
    ]

    try:
        print(f"Branding and rendering: {os.path.basename(input_path)}")
        subprocess.run(cmd, check=True)
        print(f"Success! Branded video saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e}")

if __name__ == "__main__":
    # Path updated to include 'vibes_content'
    in_file = r"C:\Project_Works\MuyProjects\video_gen_toolkits\vibes_content\recorded\raw\3660088651947857085_75056438282.mp4"
    logo_file = r"C:\Project_Works\MuyProjects\video_gen_toolkits\vibes_content\attachments\asmr-logo.png"
    out_folder = r"C:\Project_Works\MuyProjects\video_gen_toolkits\vibes_content\recorded\enhanced"
    
    enhance_with_bg_and_logo(in_file, logo_file, out_folder)