import os
from pathlib import Path

def update_script_paths():
    # --- CONFIGURATION ---
    # FIXED: Now pointing to the NEW location so the script can find the files
    target_folder = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits")
    
    old_path = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits"
    new_path = r"C:\Project_Works\MuyProjects\video_gen_toolkits"

    # --- EXECUTION ---
    if not target_folder.exists():
        print(f"❌ Error: Folder not found at {target_folder}")
        print("Please double-check that the folder name is 'MuyProjects' and not a typo.")
        return

    # Using rglob("*.py") to find scripts in the main folder AND subfolders
    py_files = list(target_folder.rglob("*.py"))
    print(f"🔍 Searching in: {target_folder}")
    print(f"🔍 Found {len(py_files)} total scripts. Starting update...")

    count = 0
    for script_path in py_files:
        try:
            # Skip this updater script itself to avoid permission issues while running
            if script_path.name == "update_script_paths.py":
                continue

            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_path in content:
                updated_content = content.replace(old_path, new_path)
                
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print(f"✅ Updated: {script_path.relative_to(target_folder)}")
                count += 1
            else:
                # Optional: print(f"➖ No change: {script_path.name}")
                pass

        except Exception as e:
            print(f"⚠️ Could not process {script_path.name}: {e}")

    print(f"\n✨ Task complete. {count} files were successfully updated to the new path.")

if __name__ == "__main__":
    update_script_paths()