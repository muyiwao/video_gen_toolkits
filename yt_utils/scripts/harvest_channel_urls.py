import yt_dlp
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

def select_input_file(directory):
    """Prompts the user to select a text file from the specific input folder."""
    txt_files = sorted(list(directory.glob("*.txt")))
    if not txt_files:
        print(f"❌ No .txt files found in {directory}")
        return None

    print("\n--- Available Input Files ---")
    for i, file in enumerate(txt_files, 1):
        print(f"{i}. {file.name}")
    
    try:
        choice = int(input(f"\nSelect a file (1-{len(txt_files)}): "))
        if 1 <= choice <= len(txt_files):
            return txt_files[choice - 1]
    except (ValueError, IndexError):
        pass
    return None

def harvest_channel_urls_only():
    """Extracts unique Channel URLs and saves them in a comma-separated format."""
    print("\n--- YouTube Channel URL Formatter ---")
    
    # --- 1. PATH CONFIGURATION ---
    input_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\text_files")
    output_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\yt_utils\yt_dls")
    
    selected_file = select_input_file(input_dir)
    if not selected_file: return

    with open(selected_file, "r", encoding="utf-8") as f:
        content = f.read()
        queries = [q.strip() for q in re.split(r'[,\n\t]+', content) if q.strip()]

    try:
        num_channels = int(input("\n🔢 Channels per query to fetch: "))
    except ValueError: return

    # --- 2. Output Preparation ---
    output_base_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = output_base_dir / f"channel_urls_{selected_file.stem}_{timestamp}.txt"

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': f"1-{num_channels}",
    }

    # --- 3. Processing ---
    unique_channel_urls = []

    print(f"\n🚀 Processing {len(queries)} queries...")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for q_idx, raw_query in enumerate(queries, 1):
            # Clean Search Query
            if "youtube.com/results" in raw_query:
                search_match = re.search(r"search_query=([^&]+)", raw_query)
                query = unquote(search_match.group(1).replace('+', ' ')) if search_match else raw_query
            else:
                query = raw_query

            print(f"   [{q_idx}/{len(queries)}] Fetching URLs for: {query}")

            try:
                search_url = f"ytsearch{num_channels}:{query}"
                result = ydl.extract_info(search_url, download=False)
                
                if 'entries' in result:
                    for entry in result['entries']:
                        if not entry: continue
                        c_id = entry.get('channel_id')
                        if c_id:
                            full_url = f"https://www.youtube.com/channel/{c_id}"
                            if full_url not in unique_channel_urls:
                                unique_channel_urls.append(full_url)
            except Exception as e:
                print(f"      ⚠️ Error: {e}")

    # --- 4. Final Formatting & Saving ---
    if unique_channel_urls:
        with open(output_filename, "w", encoding="utf-8") as f:
            # Join with comma and newline for the requested format
            f.write(",\n".join(unique_channel_urls))
        
        print(f"\n✅ SUCCESS! {len(unique_channel_urls)} unique URLs saved to:")
        print(output_filename)
    else:
        print("\n❌ No URLs were found.")

if __name__ == "__main__":
    harvest_channel_urls_only()