import os
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, ColorClip

# --- PATH CONFIGURATION ---
input_dir = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\video_pools"
bg_image_path = os.path.join(input_dir, "background.jpg") 
output_path = os.path.join(input_dir, "dancing_intro_4k_grid.mp4")
video_files = ["1.mp4", "2.mp4", "3.mp4", "4.mp4"]

# --- 4K DIMENSIONS & MATH ---
TARGET_WIDTH = 3840   # 4K UHD Width
TARGET_HEIGHT = 2160  # 4K UHD Height (16:9)
TOTAL_DURATION = 20 

# Separator Logic (2mm is approx 12px at 4K resolution)
LINE_WIDTH = 12 
# We subtract the lines from the total width to get the actual video column width
SUB_WIDTH = (TARGET_WIDTH - (LINE_WIDTH * (len(video_files) - 1))) // len(video_files)

# Timeline Settings
INTRO_DURATION = 4      
FEATURE_DURATION = 3    

# 1. Setup Background
bg = ImageClip(bg_image_path).resized(width=TARGET_WIDTH, height=TARGET_HEIGHT).with_duration(TOTAL_DURATION)

processed_layers = [bg]

for i, file_name in enumerate(video_files):
    path = os.path.join(input_dir, file_name)
    
    # Load and prep base clip for 4K
    full_vid = VideoFileClip(path).resized(height=TARGET_HEIGHT)
    v_dur = full_vid.duration
    
    w, h = full_vid.size
    # Center crop each video to fit the column width
    full_vid = full_vid.cropped(x_center=w/2, y_center=h/2, width=SUB_WIDTH, height=TARGET_HEIGHT)
    
    active_start = INTRO_DURATION + (i * FEATURE_DURATION)
    active_end = active_start + FEATURE_DURATION
    
    # Safety Buffers
    safe_p1_end = min(active_start, v_dur)
    safe_p2_start = min(active_start, v_dur - 0.1)
    safe_p2_end = min(active_end, v_dur)
    
    # --- PHASE 1: Intro/Wait ---
    p1 = (full_vid.subclipped(0, safe_p1_end)
          .with_opacity(0.5)
          .with_start(0)
          .without_audio())
    
    # --- PHASE 2: Feature Moment ---
    p2 = (full_vid.subclipped(safe_p2_start, safe_p2_end)
          .with_opacity(1.0)
          .with_start(active_start))
    
    # --- PHASE 3: Outro/Still ---
    p3 = (full_vid.to_ImageClip(t=max(0, safe_p2_end - 0.1))
          .with_opacity(0.5)
          .with_start(active_end)
          .with_duration(TOTAL_DURATION - active_end))
    
    # Calculate horizontal position including the separators
    # Pos = (Width of previous columns) + (Width of previous lines)
    x_pos = i * (SUB_WIDTH + LINE_WIDTH)
    
    column = CompositeVideoClip([p1, p2, p3]).with_position((x_pos, 0))
    
    if full_vid.audio:
        active_audio = full_vid.audio.subclipped(safe_p2_start, safe_p2_end).with_start(active_start)
        column = column.without_audio().with_audio(active_audio)
    
    processed_layers.append(column)

    # --- ADD VERTICAL SEPARATOR ---
    # Don't add a line after the last video
    if i < len(video_files) - 1:
        sep_x_pos = x_pos + SUB_WIDTH
        separator = (ColorClip(size=(LINE_WIDTH, TARGET_HEIGHT), color=(0, 0, 0))
                     .with_start(0)
                     .with_duration(TOTAL_DURATION)
                     .with_position((sep_x_pos, 0)))
        processed_layers.append(separator)

# 2. Final Assembly
final_video = CompositeVideoClip(processed_layers, size=(TARGET_WIDTH, TARGET_HEIGHT))
final_video = final_video.with_duration(TOTAL_DURATION)

# 3. Write Output
# Note: 4K rendering is CPU/GPU intensive; ensure you have enough disk space
final_video.write_videofile(
    output_path, 
    fps=30, 
    codec="libx264", 
    audio_codec="aac",
    preset="slow" # Higher quality for 4K
)

print(f"Success! 4K grid video exported to {output_path}")