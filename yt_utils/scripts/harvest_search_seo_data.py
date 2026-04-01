import yt_dlp
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

def harvest_search_seo_data():
    """
    Extracts SEO metadata with runtime filtering.
    Fixed: NoneType formatting error for view_count.
    """
    print("\n--- YouTube SEO Metadata Harvester ---")
    raw_query = input("🔎 Enter search query or URL: ").strip()
    
    try:
        num_videos = int(input("🔢 How many videos to analyze? (e.g., 5): "))
    except ValueError:
        print("❌ Invalid number.")
        return

    # --- 1. Runtime Filter Selection ---
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

    # --- 2. Query Sanitization ---
    if "youtube.com/results" in raw_query:
        search_match = re.search(r"search_query=([^&]+)", raw_query)
        query = unquote(search_match.group(1).replace('+', ' ')) if search_match else raw_query
    else:
        query = raw_query

    safe_query_name = re.sub(r'[\\/*?:"<>|]', '', query).replace(' ', '_')[:50]
    output_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\yt_utils\yt_dls")
    output_base_dir.mkdir(parents=True, exist_ok=True)
    output_filename = output_base_dir / f"seo_analysis_{safe_query_name}.txt"

    ydl_opts = {
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': f"1-{num_videos}",
        'search_sort': search_sort,
    }
    if date_filter:
        ydl_opts['dateafter'] = date_filter

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_url = f"ytsearch{num_videos}:{query}"
            print(f"\n⏳ Fetching {search_sort} results...")
            
            result = ydl.extract_info(search_url, download=False)
            if 'entries' not in result or not result['entries']:
                print("⚠️ No results found.")
                return

            videos = result['entries']

            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(f"SEO METADATA ANALYSIS REPORT\n")
                f.write(f"Search Query: {query}\n")
                f.write(f"Sorted By: {search_sort}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")

                for idx, video in enumerate(videos, 1):
                    if not video: continue
                    
                    title = video.get('title', 'N/A')
                    desc = video.get('description', 'N/A') or ""
                    tags = video.get('tags', [])
                    
                    # --- FIX: Safe extraction of views and date ---
                    views = video.get('view_count') 
                    upload_date = video.get('upload_date', 'N/A')

                    print(f"   [{idx}/{len(videos)}] Analyzing: {title[:45]}...")

                    f.write(f"VIDEO #{idx}\n")
                    f.write(f"TITLE: {title}\n")
                    # Using 'or 0' to handle None before formatting with commas
                    f.write(f"VIEWS: {views or 0:,}\n") 
                    f.write(f"UPLOAD DATE: {upload_date}\n")
                    f.write(f"URL: https://www.youtube.com/watch?v={video.get('id')}\n")
                    f.write("-" * 20 + "\n")
                    
                    desc_lines = desc.split('\n')
                    clean_desc = " ".join([l.strip() for l in desc_lines if l.strip()][:3])
                    f.write(f"CORE DESCRIPTION (SEO CONTEXT):\n{clean_desc}\n\n")
                    
                    f.write(f"TAGS / LONG-TAIL KEYWORDS:\n")
                    f.write(", ".join(tags) if tags else "None provided")
                    f.write("\n\n" + "="*60 + "\n\n")

            print(f"\n✨ DONE! SEO Report saved to:\n{output_filename}")

    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")

if __name__ == "__main__":
    harvest_search_seo_data()