import os
import shutil
import json
from pathlib import Path

def distribute_shorts_with_metadata():
    # 1. Paths Configuration
    source_dir = Path("./rain_content/output/output_shorts")
    dest_base = Path("C:\\Project_Works\\MuyVerseProjects\\youtube-content-toolkit\\Shorts")
    
    # Supported video extensions
    video_extensions = {".mp4", ".mov", ".mkv", ".webm"}

    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return

    # 2. Get and Sort Files by Creation Time (Oldest to Newest)
    files = [
        f for f in source_dir.iterdir() 
        if f.is_file() and f.suffix.lower() in video_extensions
    ]
    
    # Sort by creation time
    files.sort(key=lambda x: os.path.getctime(x))

    if not files:
        print("ℹ️ No video files found in source.")
        return

    print(f"🚀 Found {len(files)} videos. Distributing and generating metadata...")

    # 3. Process and Copy
    for index, video_path in enumerate(files, start=1):
        # Create destination folder: ./Shorts/1, ./Shorts/2, etc.
        target_folder = dest_base / str(index)
        target_folder.mkdir(parents=True, exist_ok=True)
        
        # Define destination paths
        dest_video_path = target_folder / video_path.name
        # Match the JSON filename exactly to the MP4 filename
        dest_json_path = target_folder / f"{video_path.stem}.json"

        try:
            # A. Copy the Video file
            shutil.copy2(video_path, dest_video_path)
            
            # B. Create the Empty JSON file with basic structure
            # This ensures your upload script finds the required metadata
            metadata_template = {
                "title": "",
                "description": "#shorts #rain #cozy",
                "tags": ["rain", "shorts", "ambient"],
                "privacyStatus": "public"
            }
            
            with open(dest_json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_template, f, indent=4)

            print(f"✅ [{index}] Processed: {video_path.name}")
            print(f"    - Moved to: {target_folder}")
            print(f"    - Created:  {dest_json_path.name}")

        except Exception as e:
            print(f"⚠️ Error processing {video_path.name}: {e}")

    print("\n✨ All files distributed and metadata shells created.")

if __name__ == "__main__":
    distribute_shorts_with_metadata()