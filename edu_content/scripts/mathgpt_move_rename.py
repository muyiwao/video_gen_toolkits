import shutil
import os
from pathlib import Path

def parse_range_input(range_str):
    """Parses a string like '1-5, 8, 11-13' into a list of integers [1,2,3,4,5,8,11,12,13]."""
    target_numbers = []
    # Remove spaces and split by comma
    parts = range_str.replace(" ", "").split(",")
    
    for part in parts:
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                # +1 to make the range inclusive of the end number
                target_numbers.extend(range(start, end + 1))
            except ValueError:
                print(f"Skipping invalid range: {part}")
        else:
            try:
                target_numbers.append(int(part))
            except ValueError:
                print(f"Skipping invalid number: {part}")
    
    return target_numbers

def organize_and_rename_videos():
    # 1. Define Paths
    source_dir = Path(r"C:\Users\Muy\Downloads")
    dest_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\edu_content\raw_lessons")

    # Ensure destination exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 2. Get User Input for naming range
    print("Example input: 1-10, 21-30, 33, 35-40")
    user_input = input("Enter the number sequence for renaming: ")
    name_sequence = parse_range_input(user_input)

    if not name_sequence:
        print("No valid numbers provided. Exiting.")
        return

    # 3. Move files from Downloads to Project Folder
    print("\nMoving files...")
    moved_files = []
    # Using sorted glob to maintain some order during the move process
    for file in sorted(source_dir.glob("*.mp4"), key=lambda x: x.stat().st_ctime):
        if "mathgpt-" in file.name.lower():
            try:
                target_path = dest_dir / file.name
                shutil.move(str(file), str(target_path))
                moved_files.append(target_path)
                print(f"Moved: {file.name}")
            except Exception as e:
                print(f"Error moving {file.name}: {e}")

    # 4. Filter and Sort files in destination for renaming
    # We sort by creation time to match the sequence to the order they were created/downloaded
    target_files = [f for f in dest_dir.glob("*.mp4") if "mathgpt-" in f.name.lower()]
    target_files.sort(key=lambda x: x.stat().st_ctime)

    if len(target_files) > len(name_sequence):
        print(f"\nWarning: Found {len(target_files)} files but only {len(name_sequence)} numbers provided.")
        print("Extra files will not be renamed.")

    # 5. Rename using the parsed sequence
    print("\nRenaming files based on provided sequence...")
    # zip pairs the file with the corresponding number from your list
    for old_path, num in zip(target_files, name_sequence):
        new_name = f"{num}.mp4"
        new_path = old_path.with_name(new_name)
        
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