import os

from moviepy import VideoFileClip, CompositeVideoClip, ImageClip



# Configuration

input_dir = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\video_pools"

bg_image_path = os.path.join(input_dir, "background.jpg") 

output_path = os.path.join(input_dir, "dancing_intro_20s_safe.mp4")

video_files = ["1.mp4", "2.mp4", "3.mp4", "4.mp4"]



# Dimensions

TARGET_WIDTH = 1920

TARGET_HEIGHT = 1080

SUB_WIDTH = TARGET_WIDTH // 4

TOTAL_DURATION = 20 



# Timeline Settings

INTRO_DURATION = 4      

FEATURE_DURATION = 3    



# 1. Setup Background

bg = ImageClip(bg_image_path).resized(width=TARGET_WIDTH, height=TARGET_HEIGHT).with_duration(TOTAL_DURATION)



processed_layers = [bg]



for i, file_name in enumerate(video_files):

    path = os.path.join(input_dir, file_name)

    

    # Load and prep base clip

    full_vid = VideoFileClip(path).resized(height=TARGET_HEIGHT)

    v_dur = full_vid.duration # Actual length of your file (e.g., 15.28s)

    

    w, h = full_vid.size

    full_vid = full_vid.cropped(x_center=w/2, y_center=h/2, width=SUB_WIDTH, height=TARGET_HEIGHT)

    

    # Calculate desired timing

    active_start = INTRO_DURATION + (i * FEATURE_DURATION)

    active_end = active_start + FEATURE_DURATION

    

    # SAFETY CHECK: Ensure we don't exceed the source video's length

    safe_p1_end = min(active_start, v_dur)

    safe_p2_start = min(active_start, v_dur - 0.1) # small buffer

    safe_p2_end = min(active_end, v_dur)

    

    # PHASE 1: Intro/Wait (0s to active_start)

    p1 = (full_vid.subclipped(0, safe_p1_end)

          .with_opacity(0.5)

          .with_start(0)

          .without_audio())

    

    # PHASE 2: Feature Moment (100% Opacity)

    p2 = (full_vid.subclipped(safe_p2_start, safe_p2_end)

          .with_opacity(1.0)

          .with_start(active_start))

    

    # PHASE 3: Outro/Still (active_end to 20s)

    # Freeze on the last available frame

    p3 = (full_vid.to_ImageClip(t=safe_p2_end - 0.1)

          .with_opacity(0.5)

          .with_start(active_end)

          .with_duration(TOTAL_DURATION - active_end))

    

    # Combine the phases

    column = CompositeVideoClip([p1, p2, p3]).with_position((i * SUB_WIDTH, 0))

    

    # Audio: Only during the feature segment

    if full_vid.audio:

        active_audio = full_vid.audio.subclipped(safe_p2_start, safe_p2_end).with_start(active_start)

        column = column.without_audio().with_audio(active_audio)

    

    processed_layers.append(column)



# 2. Final Assembly

final_video = CompositeVideoClip(processed_layers, size=(TARGET_WIDTH, TARGET_HEIGHT))

final_video = final_video.with_duration(TOTAL_DURATION)



# 3. Write Output

final_video.write_videofile(

    output_path, 

    fps=30, 

    codec="libx264", 

    audio_codec="aac"

)



print(f"Success! Video exported to {output_path}")