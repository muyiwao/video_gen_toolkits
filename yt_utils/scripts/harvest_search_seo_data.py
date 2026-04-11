import yt_dlp
import re
from datetime import datetime, timedelta
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
    except ValueError:
        pass
    return None

def harvest_search_seo_data():
    """Extracts SEO metadata with per-video error handling."""
    print("\n--- YouTube Resilient SEO Metadata Harvester ---")
    
    input_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\input\text_files")
    output_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\yt_utils\yt_dls")
    
    selected_file = select_input_file(input_dir)
    if not selected_file:
        return

    with open(selected_file, "r", encoding="utf-8") as f:
        content = f.read()
        queries = [q.strip() for q in re.split(r'[,\n\t]+', content) if q.strip()]

    print(f"✅ Loaded {len(queries)} items from {selected_file.name}")

    try:
        num_videos = int(input("\n🔢 Videos per query to analyze? (e.g., 5): "))
    except ValueError:
        return

    # --- Filter Selection ---
    sort_choice = input("\nSort: 1. Relevance, 2. Popularity: ").strip()
    date_choice = input("Date: 1. Any, 2. Today, 3. Week, 4. Month, 5. Year: ").strip()

    sort_map = {"1": "relevance", "2": "view_count"}
    search_sort = sort_map.get(sort_choice, "relevance")

    date_map = {"2": 0, "3": 7, "4": 30, "5": 365}
    date_filter = None
    if date_choice in date_map:
        date_limit = datetime.now() - timedelta(days=date_map[date_choice])
        date_filter = date_limit.strftime('%Y%m%d')

    output_base_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = output_base_dir / f"master_seo_report_{selected_file.stem}_{timestamp}.txt"

    # Search Options (Flat extraction to get IDs first)
    search_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': f"1-{num_videos}",
        'search_sort': search_sort,
        'ignoreerrors': True,
    }
    if date_filter:
        search_opts['dateafter'] = date_filter

    # Individual Video Options
    video_opts = {
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
    }

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("============================================================\n")
        f.write("          RESILIENT SEO METADATA REPORT\n")
        f.write("============================================================\n\n")

        for q_idx, raw_query in enumerate(queries, 1):
            if "youtube.com/results" in raw_query:
                search_match = re.search(r"search_query=([^&]+)", raw_query)
                query = unquote(search_match.group(1).replace('+', ' ')) if search_match else raw_query
            else:
                query = raw_query

            print(f"\n🔎 [{q_idx}/{len(queries)}] Searching: {query}")
            f.write(f"--- SEARCH BATCH {q_idx}: {query} ---\n\n")

            try:
                with yt_dlp.YoutubeDL(search_opts) as ydl:
                    search_url = query if query.startswith(('http', 'www')) else f"ytsearch{num_videos}:{query}"
                    search_result = ydl.extract_info(search_url, download=False)
                    video_entries = search_result.get('entries', [])

                for v_idx, entry in enumerate(video_entries, 1):
                    if not entry: continue
                    v_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                    
                    # Inner Try-Except: If one video fails, continue to next video in same query
                    try:
                        with yt_dlp.YoutubeDL(video_opts) as ydl_video:
                            video = ydl_video.extract_info(v_url, download=False)
                            
                            title = video.get('title', 'N/A')
                            desc = video.get('description', 'N/A') or ""
                            tags = video.get('tags', [])
                            views = video.get('view_count', 0)
                            upload_date = video.get('upload_date', 'N/A')

                            print(f"   [{v_idx}/{len(video_entries)}] Analyzing: {title[:40]}...")

                            f.write(f"VIDEO #{q_idx}.{v_idx}\n")
                            f.write(f"TITLE: {title}\n")
                            f.write(f"VIEWS: {views:,}\n") 
                            f.write(f"UPLOAD DATE: {upload_date}\n")
                            f.write(f"URL: {v_url}\n")
                            
                            clean_desc = " ".join([l.strip() for l in desc.split('\n') if l.strip()][:3])
                            f.write(f"CORE DESCRIPTION:\n{clean_desc}\n")
                            f.write(f"TAGS: {', '.join(tags) if tags else 'None'}\n\n")

                    except Exception as ve:
                        print(f"   [{v_idx}/{len(video_entries)}] ⚠️ Video failed: {ve}")
                        f.write(f"VIDEO #{q_idx}.{v_idx}: ❌ SKIPPED (Private or Unavailable)\n\n")
                
                f.write("*" * 40 + "\n\n")

            except Exception as qe:
                print(f"⚠️ Search failed for query {q_idx}: {qe}")
                f.write(f"❌ Error in Search Query: {qe}\n\n")

    print(f"\n✨ COMPLETE! Saved to:\n{output_filename}")

if __name__ == "__main__":
    harvest_search_seo_data()