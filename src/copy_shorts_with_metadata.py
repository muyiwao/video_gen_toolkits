import os
import shutil
from pathlib import Path

def parse_range_input(user_input):
    """Parses '1', '1-3', or '4-7' into a list of integers."""
    user_input = user_input.strip()
    if "-" in user_input:
        try:
            start, end = map(int, user_input.split("-"))
            if start > end:
                return None
            return list(range(start, end + 1))
        except ValueError:
            return None
    elif user_input.isdigit():
        return [int(user_input)]
    return None

def distribute_shorts_with_metadata():
    # 1. Paths Configuration
    source_dir = Path("./output/output_shorts")
    dest_base = Path(r"C:\Project_Works\MuyVerseProjects\youtube-content-toolkit\Shorts")
    
    video_extensions = {".mp4", ".mov", ".mkv", ".webm"}

    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return

    # 2. Get and Sort Video Files by Creation Time (to maintain 1-12 order)
    files = [
        f for f in source_dir.iterdir() 
        if f.is_file() and f.suffix.lower() in video_extensions
    ]
    files.sort(key=lambda x: os.path.getctime(x))

    if not files:
        print("ℹ️ No video files found in source.")
        return

    # 3. Runtime Range Input
    print(f"\n🚀 Found {len(files)} videos in source.")
    range_raw = input("📂 Enter destination folder range (e.g., 1-12): ").strip()
    folder_range = parse_range_input(range_raw)

    if not folder_range:
        print("❌ Invalid range format.")
        return

    # 4. Process and Move Pairs
    processed_count = 0
    for folder_num, video_path in zip(folder_range, files):
        target_folder = dest_base / str(folder_num)
        target_folder.mkdir(parents=True, exist_ok=True)
        
        # Define source and destination for the JSON pair
        source_json_path = video_path.with_suffix(".json")
        dest_video_path = target_folder / video_path.name
        dest_json_path = target_folder / source_json_path.name

        try:
            # Move the video file
            shutil.move(str(video_path), str(dest_video_path))
            
            # Move the matching JSON file if it exists
            json_status = ""
            if source_json_path.exists():
                shutil.move(str(source_json_path), str(dest_json_path))
                json_status = " + matching JSON"
            else:
                json_status = " (⚠️ No JSON found to move)"

            print(f"✅ Folder {folder_num}: {video_path.name}{json_status}")
            processed_count += 1

        except Exception as e:
            print(f"⚠️ Error moving files for folder {folder_num}: {e}")

    print(f"\n✨ Task Complete. {processed_count} pairs moved to destination folders.")

if __name__ == "__main__":
    distribute_shorts_with_metadata()