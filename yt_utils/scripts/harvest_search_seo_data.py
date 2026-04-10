import yt_dlp
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

def select_input_file(directory):
    """
    Prompts the user to select a text file from the specific input folder.
    """
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
    except ValueError:
        pass
    return None

def harvest_search_seo_data():
    """
    Extracts SEO metadata from queries/URLs provided via a selected text file.
    """
    print("\n--- YouTube Multi-Link SEO Metadata Harvester ---")
    
    # --- 1. PATH CONFIGURATION ---
    input_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\text_files")
    output_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\yt_utils\yt_dls")
    
    selected_file = select_input_file(input_dir)
    
    if not selected_file:
        print("❌ No valid file selected. Exiting.")
        return

    # Read file and split by commas, newlines, or tabs
    with open(selected_file, "r", encoding="utf-8") as f:
        content = f.read()
        queries = [q.strip() for q in re.split(r'[,\n\t]+', content) if q.strip()]

    print(f"✅ Loaded {len(queries)} items from {selected_file.name}")

    if not queries:
        print("❌ File is empty. Exiting.")
        return

    try:
        num_videos = int(input("\n🔢 How many videos per query to analyze? (e.g., 5): "))
    except ValueError:
        print("❌ Invalid number.")
        return

    # --- 2. Runtime Filter Selection ---
    print("\nSelect Search Order:")
    print("1. Relevance (Default)\n2. Popularity (View Count)")
    sort_choice = input("Selection (1-2): ").strip()
    
    print("\nSelect Upload Date Filter:")
    print("1. Any time\n2. Today\n3. This Week\n4. This Month\n5. This Year")
    date_choice = input("Selection (1-5): ").strip()

    sort_map = {"1": "relevance", "2": "view_count"}
    search_sort = sort_map.get(sort_choice, "relevance")

    date_map = {"2": 0, "3": 7, "4": 30, "5": 365}
    date_filter = None
    if date_choice in date_map:
        date_limit = datetime.now() - timedelta(days=date_map[date_choice])
        date_filter = date_limit.strftime('%Y%m%d')

    # --- 3. Output Preparation (Refactored to include input filename) ---
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract the input filename without extension (stem)
    input_stem = selected_file.stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create the new dynamic filename
    output_filename = output_base_dir / f"master_seo_report_{input_stem}_{timestamp}.txt"

    ydl_opts = {
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': f"1-{num_videos}",
        'search_sort': search_sort,
    }
    if date_filter:
        ydl_opts['dateafter'] = date_filter

    # --- 4. Processing ---
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("============================================================\n")
        f.write("          MASTER SEO METADATA ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source File: {selected_file.name}\n")
        f.write("============================================================\n\n")

        for q_idx, raw_query in enumerate(queries, 1):
            if "youtube.com/results" in raw_query:
                search_match = re.search(r"search_query=([^&]+)", raw_query)
                query = unquote(search_match.group(1).replace('+', ' ')) if search_match else raw_query
            else:
                query = raw_query

            print(f"\n🔎 [{q_idx}/{len(queries)}] Processing: {query}")
            f.write(f"--- SEARCH BATCH {q_idx}: {query} ---\n\n")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_url = query if query.startswith(('http', 'www')) else f"ytsearch{num_videos}:{query}"
                    result = ydl.extract_info(search_url, download=False)
                    
                    videos = result.get('entries', [result]) if result else []

                    for v_idx, video in enumerate(videos, 1):
                        if not video: continue
                        
                        title = video.get('title', 'N/A')
                        desc = video.get('description', 'N/A') or ""
                        tags = video.get('tags', [])
                        views = video.get('view_count', 0)
                        upload_date = video.get('upload_date', 'N/A')

                        print(f"   [{v_idx}/{len(videos)}] Analyzing: {title[:40]}...")

                        f.write(f"VIDEO #{q_idx}.{v_idx}\n")
                        f.write(f"TITLE: {title}\n")
                        f.write(f"VIEWS: {views:,}\n") 
                        f.write(f"UPLOAD DATE: {upload_date}\n")
                        f.write(f"URL: https://www.youtube.com/watch?v={video.get('id')}\n")
                        
                        desc_lines = desc.split('\n')
                        clean_desc = " ".join([l.strip() for l in desc_lines if l.strip()][:3])
                        f.write(f"CORE DESCRIPTION:\n{clean_desc}\n")
                        f.write(f"TAGS: {', '.join(tags) if tags else 'None'}\n\n")
                    
                    f.write("*" * 40 + "\n\n")

            except Exception as e:
                print(f"⚠️ Error in query {q_idx}: {e}")
                f.write(f"❌ Error extracting info for this query: {e}\n\n")

    print(f"\n✨ COMPLETE! Master SEO Report saved to:\n{output_filename}")

if __name__ == "__main__":
    harvest_search_seo_data()