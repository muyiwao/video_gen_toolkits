import os
import shutil
import json
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

    # 2. Get and Sort Files by Creation Time
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
    range_raw = input("📂 Enter destination folder range/number (e.g., 1, 1-3, 4-7): ").strip()
    folder_range = parse_range_input(range_raw)

    if not folder_range:
        print("❌ Invalid range format. Please use 'number' or 'start-end'.")
        return

    # 4. Process, Move, and Cleanup
    processed_count = 0
    for folder_num, video_path in zip(folder_range, files):
        target_folder = dest_base / str(folder_num)
        target_folder.mkdir(parents=True, exist_ok=True)
        
        dest_video_path = target_folder / video_path.name
        dest_json_path = target_folder / f"{video_path.stem}.json"
        
        # Identify the source JSON file created by the rendering script
        source_json_path = video_path.with_suffix(".json")

        try:
            # Move the video file
            shutil.move(str(video_path), str(dest_video_path))
            
            # Generate the metadata for the destination
            metadata_template = {
                "title": video_path.stem.replace("_", " "),
                "description": "#shorts #rain #cozy #ambient",
                "tags": ["rain", "shorts", "ambient", "cozy"],
                "privacyStatus": "public"
            }
            
            with open(dest_json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_template, f, indent=4)

            # --- NEW CLEANUP LOGIC ---
            # If a source JSON file exists in output_shorts, delete it
            if source_json_path.exists():
                os.remove(source_json_path)
                cleanup_msg = " (Source JSON deleted)"
            else:
                cleanup_msg = ""

            print(f"✅ Folder {folder_num}: Moved {video_path.name}{cleanup_msg}")
            processed_count += 1

        except Exception as e:
            print(f"⚠️ Error processing {video_path.name} for folder {folder_num}: {e}")

    print(f"\n✨ Task Complete. {processed_count} videos processed and source cleanup finished.")

if __name__ == "__main__":
    distribute_shorts_with_metadata()