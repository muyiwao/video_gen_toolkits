import subprocess
import os

def select_input_file_terminal(input_folder):
    """Lists available videos in the console and prompts the user for selection."""
    print(f"\n--- Select Input Video from: {os.path.basename(input_folder)} ---")
    
    supported_exts = ('.mp4', '.avi', '.mov', '.mkv')
    if not os.path.exists(input_folder):
        print(f"CRITICAL ERROR: Input directory not found: {input_folder}")
        return None

    video_files = [f for f in os.listdir(input_folder) if f.lower().endswith(supported_exts)]
    
    if not video_files:
        print("No supported video files found in the directory.")
        return None

    for idx, file_name in enumerate(video_files, start=1):
        print(f"{idx}. {file_name}")

    try:
        choice = int(input(f"Select video to process (1-{len(video_files)}): ").strip())
        if 1 <= choice <= len(video_files):
            return os.path.join(input_folder, video_files[choice - 1])
        else:
            print("Invalid selection. Exiting.")
            return None
    except ValueError:
        print("Invalid input numeric format. Exiting.")
        return None

def enhance_with_bg_and_logo(input_path, logo_path, output_dir):
    # Ensure a valid file path was chosen
    if not input_path or not os.path.exists(input_path):
        print("CRITICAL ERROR: Valid input file path missing.")
        return

    # Check if logo exists before running FFmpeg to prevent crash
    if not os.path.exists(logo_path):
        print(f"CRITICAL ERROR: Logo not found at {logo_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Keep the original file name with a branded prefix instead of overwriting
    original_name = os.path.basename(input_path)
    output_name = f"branded_{original_name}"
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
        print(f"\nBranding and rendering: {original_name}")
        subprocess.run(cmd, check=True)
        print(f"Success! Branded video saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e}")

if __name__ == "__main__":
    # Directories
    input_folder = r"C:\Project_Works\MuyProjects\video_gen_toolkits\vibes_content\recorded\raw"
    logo_file = r"C:\Project_Works\MuyProjects\video_gen_toolkits\vibes_content\attachments\asmr-logo.png"
    out_folder = r"C:\Project_Works\MuyProjects\video_gen_toolkits\vibes_content\recorded\enhanced"
    
    # 1. Prompt user to select an explicit video from the directory path
    chosen_input_file = select_input_file_terminal(input_folder)
    
    # 2. Process the chosen video asset
    if chosen_input_file:
        enhance_with_bg_and_logo(chosen_input_file, logo_file, out_folder)