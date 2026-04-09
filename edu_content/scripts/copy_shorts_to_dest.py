import shutil
import os
from pathlib import Path

def parse_range(range_str):
    """
    Parses strings like '2, 6, 10-15' into a flat list of integers.
    """
    result = set()
    parts = range_str.replace(" ", "").split(",")
    
    for part in parts:
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                result.update(range(start, end + 1))
            except ValueError:
                print(f"⚠️ Skipping invalid range: {part}")
        else:
            try:
                result.add(int(part))
            except ValueError:
                print(f"⚠️ Skipping invalid number: {part}")
    
    return sorted(list(result))

def distribute_shorts():
    # --- CONFIGURATION ---
    source_base = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\math_content\output")
    dest_base = Path(r"C:\Project_Works\MuyVerseProjects\youtube-content-toolkit\Shorts")

    print("--- YouTube Shorts File Distributor ---")
    print(f"Source: {source_base}")
    print(f"Destination Root: {dest_base}\n")

    # --- INPUT ---
    user_input = input("Enter file numbers or ranges to copy (e.g., 2, 6, 10-20): ").strip()
    file_numbers = parse_range(user_input)

    if not file_numbers:
        print("❌ No valid file numbers provided. Exiting.")
        return

    success_count = 0
    fail_count = 0

    # --- PROCESSING ---
    for num in file_numbers:
        file_name = f"{num}.mp4"
        source_file = source_base / file_name
        
        # Target Path Construction: Shorts/n/n/n.mp4
        # Based on your example: C:\...\Shorts\1\1 (I'm assuming the filename stays inside)
        target_folder = dest_base / str(num) / str(num)
        target_file = target_folder / file_name

        if source_file.exists():
            try:
                # Create destination directories if they don't exist
                target_folder.mkdir(parents=True, exist_ok=True)
                
                # Copy the file
                shutil.copy2(source_file, target_file)
                print(f"✅ Copied: {file_name} -> {target_folder}")
                success_count += 1
            except Exception as e:
                print(f"❌ Error copying {file_name}: {e}")
                fail_count += 1
        else:
            print(f"⚠️ Missing: {file_name} not found in source folder.")
            fail_count += 1

    print("\n" + "-"*30)
    print(f"DISTRIBUTION COMPLETE")
    print(f"Successfully moved: {success_count}")
    print(f"Failed/Missing: {fail_count}")
    print("-"*30)

    # Automatically open the destination root to check results
    if success_count > 0:
        os.startfile(dest_base)

if __name__ == "__main__":
    distribute_shorts()