import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

VIDEO_FOLDER = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\raw_lessons"
TOTAL_VIDEOS = 20
NUMBER_DURATION = 2
FONT_SIZE = 200
OUTPUT_FILE = os.path.join(VIDEO_FOLDER, "merged_output.mp4")

clips = []

for i in range(1, TOTAL_VIDEOS + 1):

    video_path = os.path.join(VIDEO_FOLDER, f"{i}.mp4")

    if not os.path.exists(video_path):
        print(f"Missing file: {video_path}")
        continue

    video_clip = VideoFileClip(video_path)

    number_text = TextClip(
        text=str(i),
        font_size=FONT_SIZE,
        color="white",
        size=video_clip.size
    ).with_duration(NUMBER_DURATION)

    number_clip = CompositeVideoClip(
        [number_text.with_position("center")],
        size=video_clip.size
    ).with_duration(NUMBER_DURATION)

    clips.append(number_clip)
    clips.append(video_clip)

final_video = concatenate_videoclips(clips)

final_video.write_videofile(
    OUTPUT_FILE,
    codec="libx264",
    audio_codec="aac",
    fps=30
)

print("Finished creating merged video.")