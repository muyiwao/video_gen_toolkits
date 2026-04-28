import os
from pathlib import Path

def interactive_path_picker(base_path):
    """
    Interactively navigate through subdirectories starting from a base path.
    Returns the final Path object selected by the user.
    """
    current_path = Path(base_path)
    
    # If the base path is a file (like README.md), start from its parent directory
    if current_path.is_file():
        current_path = current_path.parent

    while True:
        print(f"\n--- Current Path: {current_path} ---")
        
        # Get only directories, ignore files
        try:
            subdirs = [d for d in current_path.iterdir() if d.is_dir()]
        except PermissionError:
            print("❌ Permission Denied: Cannot access this folder.")
            return current_path

        print("0: [SELECT THIS FOLDER]")
        if current_path.parent != current_path:
            print("..: [GO BACK]")
            
        for i, folder in enumerate(subdirs, 1):
            print(f"{i}: {folder.name}")

        choice = input("\nSelect a folder number or '0' to finish: ").strip()

        if choice == '0':
            return current_path
        elif choice == '..':
            current_path = current_path.parent
            continue
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(subdirs):
                current_path = subdirs[idx]
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a number.")

# --- Example Usage (How to call it in another script) ---
if __name__ == "__main__":
    start_point = r"C:\Project_Works\YouTubeVideos\video_gen_toolkits"
    chosen_destination = interactive_path_picker(start_point)
    
    print(f"\n✅ Final Destination Path: {chosen_destination}")