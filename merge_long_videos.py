import subprocess
import os
from pathlib import Path

def sort_and_merge_videos():
    # 1. Define Path
    video_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\movie\series_1\episode_1")
    output = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\movie\series_1\episode_1\output")
    output_file = output / "final_merged_video.mp4"
    list_file = video_dir / "file_list.txt"

    if not video_dir.exists():
        print(f"Error: Directory {video_dir} not found.")
        return

    # 2. Get and Sort Videos by Creation Time
    # Filtering for .mp4 files
    videos = list(video_dir.glob("*.mp4"))
    
    # Sort by creation time (st_ctime) - earliest to latest
    videos.sort(key=lambda x: x.stat().st_ctime)

    if not videos:
        print("No .mp4 files found to merge.")
        return

    print(f"Found {len(videos)} videos. Preparing to merge...")

    # 3. Create the temporary file list for FFmpeg
    # FFmpeg concat requires a text file with lines like: file 'path/to/video.mp4'
    with open(list_file, "w", encoding="utf-8") as f:
        for video in videos:
            # We use absolute paths and handle Windows backslashes
            f.write(f"file '{video.resolve()}'\n")
            print(f"Ordered: {video.name}")

    # 4. Run FFmpeg Concat
    # -f concat: tells ffmpeg to use the concatenate demuxer
    # -safe 0: allows the use of absolute paths in the text file
    # -c copy: copies the streams without re-encoding (very fast, no quality loss)
    command = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_file)
    ]

    print("\nMerging videos (this should be fast)...")
    result = subprocess.run(command, capture_output=True, text=True)

    # 5. Cleanup and Results
    if result.returncode == 0:
        print(f"\nSuccess! Final video saved as: {output_file.name}")
        # Delete the temporary list file
        if list_file.exists():
            list_file.unlink()
    else:
        print(f"\nFFmpeg Error:\n{result.stderr}")

if __name__ == "__main__":
    sort_and_merge_videos()