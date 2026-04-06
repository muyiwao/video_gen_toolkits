import yt_dlp
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

def harvest_search_seo_data():
    """
    Extracts SEO metadata from multiple search queries/URLs into a single report.
    """
    print("\n--- YouTube Multi-Link SEO Metadata Harvester ---")
    
    # --- 1. Collect Multiple Queries ---
    queries = []
    print("Enter your search queries or YouTube URLs (one per line).")
    print("Type 'DONE' or leave blank and press Enter when finished:")
    while True:
        entry = input(f" > Item {len(queries) + 1}: ").strip()
        if not entry or entry.upper() == 'DONE':
            break
        queries.append(entry)

    if not queries:
        print("❌ No queries entered. Exiting.")
        return

    try:
        num_videos = int(input("\n🔢 How many videos per query to analyze? (e.g., 5): "))
    except ValueError:
        print("❌ Invalid number.")
        return

    # --- 2. Runtime Filter Selection (Applied to all) ---
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

    # --- 3. Output Path Configuration ---
    output_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\yt_utils\yt_dls")
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a unique name for the single master file based on the first query and timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = output_base_dir / f"master_seo_report_{timestamp}.txt"

    ydl_opts = {
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': f"1-{num_videos}",
        'search_sort': search_sort,
    }
    if date_filter:
        ydl_opts['dateafter'] = date_filter

    # --- 4. Process all queries into one file ---
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("============================================================\n")
        f.write("           MASTER SEO METADATA ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Filters: Sort by {search_sort}, Date filter: {date_choice}\n")
        f.write("============================================================\n\n")

        for q_idx, raw_query in enumerate(queries, 1):
            # Query Sanitization
            if "youtube.com/results" in raw_query:
                search_match = re.search(r"search_query=([^&]+)", raw_query)
                query = unquote(search_match.group(1).replace('+', ' ')) if search_match else raw_query
            else:
                query = raw_query

            print(f"\n🔎 [{q_idx}/{len(queries)}] Processing: {query}")
            f.write(f"--- SEARCH BATCH {q_idx}: {query} ---\n\n")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_url = f"ytsearch{num_videos}:{query}"
                    result = ydl.extract_info(search_url, download=False)
                    
                    if 'entries' not in result or not result['entries']:
                        f.write("⚠️ No results found for this query.\n\n")
                        continue

                    videos = result['entries']

                    for v_idx, video in enumerate(videos, 1):
                        if not video: continue
                        
                        title = video.get('title', 'N/A')
                        desc = video.get('description', 'N/A') or ""
                        tags = video.get('tags', [])
                        views = video.get('view_count') 
                        upload_date = video.get('upload_date', 'N/A')

                        print(f"   [{v_idx}/{len(videos)}] Analyzing: {title[:40]}...")

                        f.write(f"VIDEO #{q_idx}.{v_idx}\n")
                        f.write(f"TITLE: {title}\n")
                        f.write(f"VIEWS: {views or 0:,}\n") 
                        f.write(f"UPLOAD DATE: {upload_date}\n")
                        f.write(f"URL: https://www.youtube.com/watch?v={video.get('id')}\n")
                        
                        desc_lines = desc.split('\n')
                        clean_desc = " ".join([l.strip() for l in desc_lines if l.strip()][:3])
                        f.write(f"CORE DESCRIPTION:\n{clean_desc}\n")
                        
                        f.write(f"TAGS:\n")
                        f.write(", ".join(tags) if tags else "None")
                        f.write("\n\n")
                    
                    f.write("*" * 40 + "\n\n")

            except Exception as e:
                print(f"⚠️ Error in query {q_idx}: {e}")
                f.write(f"❌ Error extracting info for this query: {e}\n\n")

    print(f"\n✨ COMPLETE! Master SEO Report saved to:\n{output_filename}")

if __name__ == "__main__":
    harvest_search_seo_data()