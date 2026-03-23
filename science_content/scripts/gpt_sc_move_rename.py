import shutil
import os
from pathlib import Path

def organize_and_rename_videos():
    # 1. Define Paths
    source_dir = Path(r"C:\Users\Muy\Downloads\raw")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\muyverse_maths\curated")

    # Ensure destination exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 2. Move files from Downloads to Project Folder
    print("Moving files...")
    for file in source_dir.glob("*.mp4"):
        if "mathgpt-" in file.name.lower():
            try:
                shutil.move(str(file), str(dest_dir / file.name))
                print(f"Moved: {file.name}")
            except Exception as e:
                print(f"Error moving {file.name}: {e}")

    # 3. Collect moved files in the destination for renaming
    # We re-scan the destination to ensure we have the full list
    target_files = [f for f in dest_dir.glob("*.mp4") if "mathgpt-" in f.name.lower()]

    # 4. Sort by creation time (oldest first)
    target_files.sort(key=lambda x: x.stat().st_ctime)

    # 5. Rename to 1.mp4, 2.mp4, etc.
    print("\nRenaming files sequentially...")
    for index, old_path in enumerate(target_files, start=1):
        new_name = f"{index}.mp4"
        new_path = old_path.with_name(new_name)
        # Check if 1.mp4, 2.mp4 etc already exists to avoid overwriting errors
        if new_path.exists():
            print(f"Skipping {new_name}: File already exists.")
            continue
        try:
            old_path.rename(new_path)
            print(f"Renamed: {old_path.name} -> {new_name}")
        except Exception as e:
            print(f"Error renaming {old_path.name}: {e}")

    print("\nTask complete.")

if __name__ == "__main__":
    organize_and_rename_videos()