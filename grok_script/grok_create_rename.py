import os
from pathlib import Path

def rename_videos_sequentially():
    try:
        # 1. Gather User Input
        s = int(input("Enter Season (s) number: "))
        e = int(input("Enter Episode (e) number: "))
        # Path where your 'grok-' files are located
        target_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\movie\series_1\episode_1")

        if not target_dir.exists():
            print(f"Error: Directory {target_dir} does not exist.")
            return

        # 2. Collect and Sort Files
        # Filter for .mp4 files containing "grok-"
        files = [f for f in target_dir.glob("*.mp4") if "grok-" in f.name]
        
        # Sort by creation time (st_ctime) - oldest first
        files.sort(key=lambda x: x.stat().st_ctime)

        if not files:
            print("No matching 'grok-' mp4 files found.")
            return

        print(f"\n--- Renaming {len(files)} files ---\n")

        # 3. Rename Files Sequentially
        for i, old_file_path in enumerate(files, start=1):
            new_name = f"s{s}_e{e}_v{i:02d}.mp4"
            new_file_path = old_file_path.with_name(new_name)
            
            # Perform the rename
            old_file_path.rename(new_file_path)
            print(f"Renamed: {old_file_path.name} -> {new_name}")

        print("\nAll files renamed successfully.")

    except ValueError:
        print("Error: Please enter valid integers for Season and Episode.")
    except Exception as error:
        print(f"An unexpected error occurred: {error}")

if __name__ == "__main__":
    rename_videos_sequentially()