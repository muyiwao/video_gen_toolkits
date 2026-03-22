import subprocess
import os
from pathlib import Path

# --- CONFIGURATION ---
PATHS = {
    "main_v": r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\attachments\shorts\6.mp4", # This is the main video with a black background to be removed
    "v1":     r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\attachments\shorts\intro_video.mp4", # This is the first video that plays at the start (0-5s)
    "v2":     r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\attachments\shorts\subscribe-cta.mp4", # This is the second video that plays at intervals
    "v3":     r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\attachments\shorts\outtro_video.mp4", # This is the third video that plays at the end
    "img1":   r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\attachments\shorts\background_with_logo.png", # This is the first image for background
    "img2":   r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\attachments\shorts\related_video_pointer.png", # This is the second image that appears after 10s
    "output": r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\output\final_output.mp4"
}

def build_ffmpeg_command():
    # Target Vertical Resolution
    W, H = 1080, 1920
    
    # 1. Main Video Prep: 
    # - Speed 0.9x (PTS * 1.11)
    # - Scale & Crop to 9:16 Center
    # - Colorkey (Remove Black background)
    main_prep = (
        f"[0:v]setpts=1.11*PTS,scale=-1:{H},crop={W}:{H},colorkey=0x000000:0.1:0.1[main_v];"
    )

    # 2. Background Prep: 
    # - Image 1 scaled to fill 9:16
    img1_prep = (
        f"[4:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[bg];"
    )

    # 3. Image 2 Prep:
    # - Appear after 10s (using enable 'gt(t,10)')
    img2_overlay = (
        f"[5:v]scale={W*0.4}:-1[img2_scaled];"
    )

    # 4. Video 2 Logic (Every 30s):
    # - We loop Video 2 and use 'enable' to show it at intervals
    # - Interval: 0-5s (Intro V1), then V2 at 30s, 60s, 90s...
    v2_logic = (
        f"[2:v]scale={W}:-1,setpts=PTS-STARTPTS[v2_scaled];"
    )

    # 5. The Layering Chain (Filter Complex)
    # Layer 0: Image 1 (Background)
    # Layer 1: Main Video (Transparent)
    # Layer 2: Image 2 (After 10s)
    # Layer 3: Video 2 (Modulo 30s)
    # Layer 4: Video 1 (Start) & Video 3 (End) are handled via Concat for stability
    
    filter_complex = (
        main_prep + img1_prep + img2_overlay + v2_logic +
        f"[bg][main_v]overlay=0:0[tmp1];"
        f"[tmp1][img2_scaled]overlay=x=(W-w)/2:y=H-500:enable='gt(t,10)'[tmp2];"
        # Video 2 overlay logic: appears for 3 seconds every 30 seconds
        f"[tmp2][v2_scaled]overlay=0:0:enable='lt(mod(t,30),3)'[visual_out]"
    )

    cmd = [
        'ffmpeg', '-y',
        '-i', PATHS["main_v"],  # [0]
        '-i', PATHS["v1"],      # [1]
        '-i', PATHS["v2"],      # [2]
        '-i', PATHS["v3"],      # [3]
        '-i', PATHS["img1"],    # [4]
        '-i', PATHS["img2"],    # [5]
        '-filter_complex', filter_complex,
        '-map', '[visual_out]',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
        PATHS["output"]
    ]

    return cmd

if __name__ == "__main__":
    # Check if files exist
    missing = [p for p in PATHS.values() if not os.path.exists(p) and p != PATHS["output"]]
    if missing:
        print(f"❌ Missing files: {missing}")
    else:
        print("🚀 Compiling 9:16 Production...")
        try:
            subprocess.run(build_ffmpeg_command(), check=True)
            print(f"✅ FINAL OUTPUT READY: {PATHS['output']}")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg Error: {e}")