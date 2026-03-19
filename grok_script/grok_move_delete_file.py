import os
import shutil
from pathlib import Path

def organize_episode_files():
    # Define source and destination paths
    # Update 'source_folder' to the directory where your Grok videos are currently located
    source_folder = Path(r'C:\Users\Muy\Downloads')
    dest_folder = Path(r'C:\Project_Works\YouTubeVideos\video_gen_toolkits\movie\series_1\episode_1')

    # Ensure the destination directory exists
    if not dest_folder.exists():
        dest_folder.mkdir(parents=True, exist_ok=True)
        print(f"Created destination directory: {dest_folder}")

    # 1. Delete any existing .png files in the destination folder
    for png_file in dest_folder.glob("*.png"):
        try:
            png_file.unlink()
            print(f"Deleted old frame: {png_file.name}")
        except Exception as e:
            print(f"Error deleting {png_file.name}: {e}")

    # 2. Find and move .mp4 files containing "grok-" in the filename
    moved_count = 0
    for mp4_file in source_folder.glob("*.mp4"):
        if "grok" in mp4_file.name:
            try:
                # Use shutil.move to transfer the file
                shutil.move(str(mp4_file), str(dest_folder / mp4_file.name))
                print(f"Moved: {mp4_file.name}")
                moved_count += 1
            except Exception as e:
                print(f"Error moving {mp4_file.name}: {e}")

    print(f"\nTask Complete. {moved_count} files moved to {dest_folder}.")

if __name__ == "__main__":
    organize_episode_files()