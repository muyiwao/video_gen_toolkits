import os
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, AudioFileClip

# Configuration
input_dir = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\video_pools"
output_path = os.path.join(input_dir, "dancing_intro_4K_final.mp4")
video_files = ["1.mp4", "2.mp4", "3.mp4", "4.mp4"]
end_video_file = os.path.join(input_dir, "end_video.mp4")
audio_file = os.path.join(input_dir, "intro_sound.mp3")

# 4K Dimensions
TARGET_WIDTH = 3840
TARGET_HEIGHT = 2160
SUB_WIDTH = TARGET_WIDTH // 4
TOTAL_DURATION = 20 

# Timeline Settings
INTRO_DURATION = 4      # 0-4s: All at 50%
FEATURE_DURATION = 3    # 4-16s: 100% staggered (4 clips * 3s)

# 1. Setup Background using frame at 16s from the first video
first_vid_path = os.path.join(input_dir, video_files[0])
with VideoFileClip(first_vid_path) as temp_clip:
    # Taking the frame at 16s (or the very end if shorter)
    bg_frame_time = min(16, temp_clip.duration - 0.1)
    bg = (temp_clip.to_ImageClip(t=bg_frame_time)
          .resized(width=TARGET_WIDTH, height=TARGET_HEIGHT)
          .with_duration(TOTAL_DURATION))

processed_layers = [bg]

# 2. Process the 4 Dancing Columns
for i, file_name in enumerate(video_files):
    path = os.path.join(input_dir, file_name)
    
    # Load and prep base clip to 4K height
    full_vid = VideoFileClip(path).resized(height=TARGET_HEIGHT)
    
    # Crop to 1/4th of 4K width (960px)
    w, h = full_vid.size
    full_vid = full_vid.cropped(x_center=w/2, y_center=h/2, width=SUB_WIDTH, height=TARGET_HEIGHT)
    
    # Timing calculations
    active_start = INTRO_DURATION + (i * FEATURE_DURATION)
    active_end = active_start + FEATURE_DURATION
    
    # PHASE 1: 0s to active_start (50% Opacity)
    p1 = (full_vid.subclipped(0, active_start)
          .with_opacity(0.5)
          .with_start(0))
    
    # PHASE 2: Feature Moment (100% Opacity)
    p2 = (full_vid.subclipped(active_start, active_end)
          .with_opacity(1.0)
          .with_start(active_start))
    
    # PHASE 3: Still until 16s (50% Opacity)
    # We stop the columns at 16s to make room for the end_video overlay
    p3 = (full_vid.to_ImageClip(t=active_end - 0.1)
          .with_opacity(0.5)
          .with_start(active_end)
          .with_duration(16 - active_end))
    
    column = CompositeVideoClip([p1, p2, p3]).with_position((i * SUB_WIDTH, 0)).without_audio()
    processed_layers.append(column)

# 3. Add End Video Overlay (16s - 20s)
end_vid = (VideoFileClip(end_video_file)
           .resized(width=TARGET_WIDTH) # Fit to 4K width
           .with_start(16)
           .with_duration(4)
           .with_position("center"))
processed_layers.append(end_vid)

# 4. Final Assembly & Background Audio
final_video = CompositeVideoClip(processed_layers, size=(TARGET_WIDTH, TARGET_HEIGHT))

# Global Soundtrack
bg_music = AudioFileClip(audio_file).subclipped(0, TOTAL_DURATION)
final_video = final_video.with_audio(bg_music).with_duration(TOTAL_DURATION)

# 5. Write 4K Output
final_video.write_videofile(
    output_path, 
    fps=30, 
    codec="libx264", 
    audio_codec="aac",
    preset="slow" # Better quality for 4K
)

print(f"Success! 4K Intro saved at: {output_path}")