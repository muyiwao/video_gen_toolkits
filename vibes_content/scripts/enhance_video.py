import subprocess
import os

def enhance_with_blurred_bg(input_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_name = "ultra_crispy_blurred_bg.mp4"
    output_path = os.path.join(output_dir, output_name)
    
    # FILTER GRAPH:
    # 1. Takes the landscape content, blurs and scales it to fill the background.
    # 2. Takes the landscape content, sharpens it, and overlays it on the center.
    filter_complex = (
        "[0:v]crop=iw:iw*9/16[base];"
        "[base]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg];"
        "[0:v]crop=iw:iw*9/16,scale=1080:-1:flags=lanczos,unsharp=5:5:1.2:5:5:0.0[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
    )
    
    cmd = [
        'ffmpeg', '-i', input_path,
        '-filter_complex', filter_complex,
        '-map', '[v]',          # Maps the visual output
        '-map', '0:a?',         # Corrected: Separate arguments for audio
        '-c:v', 'libx264', 
        '-crf', '16',           # High bitrate for crispness
        '-preset', 'slow',      # 'slow' is usually the sweet spot for quality vs time
        '-pix_fmt', 'yuv420p',  # Compatibility fix
        '-y', output_path
    ]

    try:
        print(f"Processing: {os.path.basename(input_path)}")
        subprocess.run(cmd, check=True)
        print(f"Success! Output saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e}")

if __name__ == "__main__":
    in_file = r"C:\Project_Works\MuyProjects\video_gen_toolkits\vibes_content\recorded\raw\3660088651947857085_75056438282.mp4"
    out_folder = r"C:\Project_Works\MuyProjects\video_gen_toolkits\vibes_content\recorded\enhanced"
    
    enhance_with_blurred_bg(in_file, out_folder)