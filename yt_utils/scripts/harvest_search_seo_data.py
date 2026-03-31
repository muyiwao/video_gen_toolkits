import yt_dlp
import re
from datetime import datetime
from pathlib import Path

def harvest_search_seo_data():
    """
    Extracts SEO metadata (Title, Description, Tags) from top N results.
    Fixes: Filename 'Invalid argument' error and URL-to-Query conversion.
    """
    print("\n--- YouTube SEO Metadata Harvester ---")
    raw_query = input("🔎 Enter search query or URL: ").strip()
    
    try:
        num_videos = int(input("🔢 How many top videos to analyze? (e.g., 5): "))
    except ValueError:
        print("❌ Please enter a valid number.")
        return

    if not raw_query:
        print("❌ No query detected.")
        return

    # --- FIX 1: Extract keywords if a URL is pasted ---
    # If the user pastes "https://...&search_query=Rain+Sounds", extract "Rain Sounds"
    if "youtube.com/results" in raw_query:
        search_match = re.search(r"search_query=([^&]+)", raw_query)
        if search_match:
            query = search_match.group(1).replace('+', ' ')
            from urllib.parse import unquote
            query = unquote(query)
        else:
            query = raw_query
    else:
        query = raw_query

    # --- FIX 2: Sanitize Filename ---
    # Remove characters that Windows forbids: \ / : * ? " < > |
    safe_query_name = re.sub(r'[\\/*?:"<>|]', '', query).replace(' ', '_')[:50]
    
    output_base_dir = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\yt_utils\yt_dls")
    output_base_dir.mkdir(parents=True, exist_ok=True)
    output_filename = output_base_dir / f"seo_analysis_{safe_query_name}.txt"

    ydl_opts = {
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': f"1-{num_videos}",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearchN:query is the syntax to trigger a search
            search_url = f"ytsearch{num_videos}:{query}"
            
            print(f"\n⏳ Fetching SEO data for: '{query}'...")
            result = ydl.extract_info(search_url, download=False)

            if 'entries' not in result or not result['entries']:
                print("⚠️ No results found.")
                return

            videos = result['entries']

            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(f"SEO METADATA ANALYSIS REPORT\n")
                f.write(f"Search Query: {query}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")

                for idx, video in enumerate(videos, 1):
                    # Ensure video is a dictionary (sometimes yt-dlp returns None for deleted videos)
                    if not video: continue
                    
                    title = video.get('title', 'N/A')
                    desc = video.get('description', 'N/A') or ""
                    tags = video.get('tags', [])
                    
                    print(f"   [{idx}/{len(videos)}] Analyzing: {title[:45]}...")

                    f.write(f"VIDEO #{idx}\n")
                    f.write(f"TITLE: {title}\n")
                    f.write(f"URL: https://www.youtube.com/watch?v={video.get('id')}\n")
                    f.write("-" * 20 + "\n")
                    
                    # SEO Strategy: Extract first 3 lines (Primary Context)
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