import re
import os
import sys
from pathlib import Path
from datetime import datetime

# --- DEPENDENCY CHECK ---
try:
    from YoutubeTags import channeltags
except ImportError:
    print("\n❌ ERROR: 'YoutubeTags' library not found.")
    print("Please run the following command to install it:")
    print(f"{sys.executable} -m pip install YoutubeTags")
    sys.exit(1)

def select_input_file(directory):
    """Prompts user to select the channel URL list file."""
    txt_files = sorted(list(directory.glob("*.txt")))
    if not txt_files:
        print(f"❌ No .txt files found in {directory}")
        return None

    print("\n--- Select Channel URL List ---")
    for i, file in enumerate(txt_files, 1):
        print(f"{i}. {file.name}")
    
    try:
        choice = int(input(f"\nSelect file (1-{len(txt_files)}): "))
        if 1 <= choice <= len(txt_files):
            return txt_files[choice - 1]
    except (ValueError, IndexError):
        pass
    return None

def harvest_channel_keywords():
    """Reads channel URLs, extracts keywords, and deletes input file upon success."""
    print("\n--- YouTube Channel Keyword Harvester ---")
    
    # --- 1. PATH CONFIGURATION ---
    # Looking in the utility folder where URLs were saved
    input_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\yt_utils\yt_dls")
    output_dir = input_dir 
    
    selected_file = select_input_file(input_dir)
    if not selected_file:
        return

    # --- 2. PARSING URLS ---
    try:
        with open(selected_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Handles commas and newlines from the previous script's output
            urls = [u.strip() for u in re.split(r'[,\n]+', content) if u.strip()]
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    if not urls:
        print("❌ No URLs found in the selected file.")
        return

    # --- 3. OUTPUT PREPARATION ---
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = output_dir / f"keywords_{selected_file.stem}_{timestamp}.txt"

    print(f"\n🚀 Extracting keywords for {len(urls)} channels...")
    
    # --- 4. PROCESSING LOOP ---
    success_count = 0

    with open(output_filename, "w", encoding="utf-8") as f_out:
        f_out.write(f"CHANNEL KEYWORD REPORT - {datetime.now()}\n")
        f_out.write(f"Source: {selected_file.name}\n")
        f_out.write("="*60 + "\n\n")

        for i, url in enumerate(urls, 1):
            print(f"   [{i}/{len(urls)}] Analyzing: {url}")
            try:
                # Core keyword extraction
                keywords = channeltags(url)
                
                f_out.write(f"URL: {url}\n")
                f_out.write(f"KEYWORDS: {keywords if keywords else 'No keywords found'}\n")
                f_out.write("-" * 30 + "\n")
                success_count += 1
            except Exception as e:
                print(f"      ⚠️ Failed {url}: {e}")
                f_out.write(f"URL: {url}\n")
                f_out.write(f"ERROR: Could not retrieve tags ({e})\n")
                f_out.write("-" * 30 + "\n")

    # --- 5. AUTOMATIC CLEANUP ---
    # Only delete if we successfully processed the list
    if success_count > 0:
        print(f"\n✅ SUCCESS! Keywords saved to: {output_filename.name}")
        try:
            # Explicitly close any possible handles (though 'with' handles this)
            os.remove(str(selected_file))
            print(f"🗑️ Input file deleted: {selected_file.name}")
        except Exception as e:
            print(f"⚠️ Process finished but could not delete input file: {e}")
    else:
        print("\n❌ Processing failed for all URLs. Input file was not deleted.")

if __name__ == "__main__":
    harvest_channel_keywords()