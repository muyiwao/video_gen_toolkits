import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# Target resolution for 720p
TARGET_RES = (1280, 720) 

VIDEO_FOLDER = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\edu_content\raw_lessons"
TOTAL_VIDEOS = 10
NUMBER_DURATION = 2
FONT_SIZE = 200
OUTPUT_FILE = os.path.join(VIDEO_FOLDER, "merged_output.mp4")

clips = []

for i in range(1, TOTAL_VIDEOS + 1):
    video_path = os.path.join(VIDEO_FOLDER, f"{i}.mp4")

    if not os.path.exists(video_path):
        print(f"Missing file: {video_path}")
        continue

    # Load and resize the source video to 720p
    video_clip = VideoFileClip(video_path).resized(TARGET_RES)

    # Create the text clip at the target 720p size
    number_text = TextClip(
        text=str(i),
        font_size=FONT_SIZE,
        color="white",
        size=TARGET_RES  # Match resolution here
    ).with_duration(NUMBER_DURATION)

    number_clip = CompositeVideoClip(
        [number_text.with_position("center")],
        size=TARGET_RES
    ).with_duration(NUMBER_DURATION)

    clips.append(number_clip)
    clips.append(video_clip)

# Concatenate all clips (all are now uniform 720p)
final_video = concatenate_videoclips(clips, method="compose")

final_video.write_videofile(
    OUTPUT_FILE,
    codec="libx264",
    audio_codec="aac",
    fps=30
)

print(f"Finished creating merged video at {TARGET_RES[0]}x{TARGET_RES[1]}.")