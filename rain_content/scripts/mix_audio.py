import subprocess
import math
from pathlib import Path

def select_subfolder(base_path, prompt):
    """Lists subdirectories within the base path for selection."""
    subfolders = [f for f in base_path.iterdir() if f.is_dir()]
    if not subfolders:
        print(f"No subfolders found in {base_path}")
        return base_path

    print(f"\n--- {prompt} ---")
    for idx, folder in enumerate(subfolders, 1):
        print(f"{idx}. {folder.name}")
    
    try:
        choice = int(input(f"Select a folder (1-{len(subfolders)}): "))
        return subfolders[choice - 1]
    except (ValueError, IndexError):
        print("Invalid choice, searching in base path instead.")
        return base_path

def select_file(directory, prompt):
    """Interactive file selector for the selected directory."""
    files = list(Path(directory).glob("*.mp3"))
    if not files:
        print(f"No MP3 files found in {directory}")
        return None

    print(f"\n--- {prompt} ---")
    for idx, file in enumerate(files, 1):
        print(f"{idx}. {file.name}")
    
    try:
        choice = int(input(f"Select a file (1-{len(files)}): "))
        return files[choice - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None

def mix_audio():
    # 1. Path Configurations
    base_path = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\input\audio_pools")
    output_dir = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\input\audio_pools\sfx")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Sequential Selection for Sound 1
    folder1 = select_subfolder(base_path, "Choose Category for Sound 1")
    audio1 = select_file(folder1, f"Select File from {folder1.name}")
    if not audio1: return
    
    # 3. Sequential Selection for Sound 2
    folder2 = select_subfolder(base_path, "Choose Category for Sound 2")
    audio2 = select_file(folder2, f"Select File from {folder2.name}")
    if not audio2: return

    # 4. Percentage Inputs
    try:
        print("\n--- Volume Proportions (Decimal) ---")
        vol1 = float(input(f"Enter volume for {audio1.name} (e.g., 0.625): "))
        vol2 = float(input(f"Enter volume for {audio2.name} (e.g., 0.375): "))
    except ValueError:
        print("❌ Invalid decimal input.")
        return

    # 5. Output Configuration
    out_name = input("\nEnter name for output file (without .mp3): ").strip() or "combined_mix"
    output_path = output_dir / f"{out_name}.mp3"

    # 6. FFmpeg Command with Looping Support
    # '-stream_loop -1' ensures shorter clips repeat to match the longer clip
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(audio1),
        "-stream_loop", "-1", "-i", str(audio2),
        "-filter_complex", 
        f"[0:a]volume={vol1}[a1];[1:a]volume={vol2}[a2];[a1][a2]amix=inputs=2:duration=shortest:dropout_transition=0",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        str(output_path)
    ]

    print(f"\n🎵 Mixing: {vol1*100}% {audio1.name} + {vol2*100}% {audio2.name}...")
    
    try:
        # Note: We use duration=shortest in the amix filter combined with loop 
        # to ensure the mix doesn't run infinitely, though in this case, 
        # you may need to manually stop or define a -t (time) if both loop.
        # For a standard mix, we'll remove infinite loop and stick to longest:
        
        final_cmd = [
            "ffmpeg", "-y",
            "-i", str(audio1),
            "-i", str(audio2),
            "-filter_complex", 
            f"[0:a]volume={vol1}[a1];[1:a]volume={vol2}[a2];[a1][a2]amix=inputs=2:duration=longest:dropout_transition=0",
            "-c:a", "libmp3lame", "-q:a", "2", str(output_path)
        ]
        
        subprocess.run(final_cmd, check=True, capture_output=True)
        print(f"✅ Success! Saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr.decode()}")

if __name__ == "__main__":
    mix_audio()