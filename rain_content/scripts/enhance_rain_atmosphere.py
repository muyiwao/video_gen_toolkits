import subprocess
from pathlib import Path

def select_input_files(directory):
    """Allows user to select single, multiple, or all files for processing."""
    exts = {
        "1": (".jpg", ".jpeg", ".png", ".webp", ".bmp"), # Image
        "2": (".mp4", ".mov", ".mkv", ".avi")          # Video
    }
    
    print("\n--- Input Type Selection ---")
    print("1. Images")
    print("2. Videos")
    type_choice = input("Select input type (1 or 2): ").strip()
    
    if type_choice not in exts:
        print("❌ Invalid type selection.")
        return [], None
    
    valid_exts = exts[type_choice]
    input_type = "image" if type_choice == "1" else "video"
    
    # Filter and list files
    files = sorted([f for f in directory.glob("*") if f.suffix.lower() in valid_exts])
    
    if not files:
        print(f"❌ No matching files found in: {directory}")
        return [], None

    print(f"\n--- Available {input_type.capitalize()}s ---")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file.name}")
    
    print("\nSelection Options:")
    print("- Single: '1'")
    print("- Multiple: '1, 3, 5'")
    print("- All: 'all'")
    
    user_input = input("\nEnter your selection: ").strip().lower()
    
    selected_files = []
    if user_input == 'all':
        selected_files = files
    else:
        try:
            indices = [int(i.strip()) - 1 for i in user_input.split(',')]
            selected_files = [files[i] for i in indices if 0 <= i < len(files)]
        except ValueError:
            print("❌ Invalid format. Use numbers separated by commas.")
            return [], None

    return selected_files, input_type

def run_ffmpeg_process(input_file, output_path, input_type, color_grading):
    """Handles the actual FFmpeg call for an individual file."""
    cmd = ["ffmpeg", "-y", "-i", str(input_file)]

    if input_type == "video":
        # Extract the first high-quality frame
        cmd += ["-frames:v", "1"]

    cmd += [
        "-vf", color_grading,
        "-q:v", "2", 
        str(output_path)
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error processing {input_file.name}: {e.stderr.decode()}")
        return False

def enhance_rain_atmosphere():
    # 1. Path Configuration
    raw_dir = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\raw")
    enhanced_dir = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\enhanced")
    enhanced_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Runtime Selection
    selected_files, input_type = select_input_files(raw_dir)
    if not selected_files:
        print("No files selected. Exiting.")
        return

    # 3. Atmospheric Filter (Payne's Gray / Moody Ultramarine)
    color_grading = (
        "colorchannelmixer="
        ".75:.1:.1:0: "   # Muting Reds
        "0:.85:.2:0: "    # Deepening Greens
        "0:.25:1.25:0, "  # Boosting Blues/Violets
        "eq=brightness=-0.06:contrast=1.2:saturation=0.8, "
        "unsharp=5:5:0.7:5:5:0.0"
    )

    print(f"\n🚀 Starting batch process for {len(selected_files)} items...")

    # 4. Loop Processing
    success_count = 0
    for file in selected_files:
        output_path = enhanced_dir / f"Enhanced_{file.stem}.jpg"
        print(f"✨ Enhancing: {file.name} -> {output_path.name}")
        
        if run_ffmpeg_process(file, output_path, input_type, color_grading):
            success_count += 1

    print(f"\n✅ Finished! Successfully processed {success_count}/{len(selected_files)} files.")
    print(f"👉 Location: {enhanced_dir}")

if __name__ == "__main__":
    enhance_rain_atmosphere()