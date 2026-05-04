import yt_dlp
import re
from datetime import datetime, timedelta
from pathlib import Path

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
    """Extracts SEO metadata with strict date, subscriber, and view filters."""
    print("\n--- YouTube Underdog SEO Harvester ---")
    
    input_dir = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\input\text_files")
    output_base_dir = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\yt_utils\yt_dls")
    
    selected_file = select_input_file(input_dir)
    if not selected_file:
        return

    with open(selected_file, "r", encoding="utf-8") as f:
        content = f.read()
        queries = [q.strip() for q in re.split(r'[,\n\t]+', content) if q.strip()]

    print(f"✅ Loaded {len(queries)} items from {selected_file.name}")

    # --- Runtime Configuration ---
    try:
        num_to_scan = int(input("\n🔢 How many top videos to SCAN per query? (e.g., 50): ") or 50)
        
        sub_input = input("👥 Max Subscriber Limit? [Default 100000]: ").strip()
        sub_limit = int(sub_input) if sub_input else 100000

        # NEW: View Count Filter
        view_input = input("📈 Min View Count? [Default 1000]: ").strip()
        min_views = int(view_input) if view_input else 1000

        print("\n📅 Select Search Date Range:")
        print("1. Past Week")
        print("2. Past Month")
        print("3. Past Year")
        print("4. All Time")
        date_choice = input("Choice (1-4): ").strip()
        
        date_map = {"1": 7, "2": 30, "3": 365}
        
        cutoff_date_obj = None
        date_filter_str = None
        
        if date_choice in date_map:
            cutoff_date_obj = datetime.now() - timedelta(days=date_map[date_choice])
            date_filter_str = cutoff_date_obj.strftime('%Y%m%d')
        else:
            date_filter_str = None

    except ValueError:
        print("❌ Invalid input. Using defaults.")
        num_to_scan, sub_limit, min_views, cutoff_date_obj, date_filter_str = 50, 100000, 1000, None, None

    output_base_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = output_base_dir / f"underdog_seo_report_{selected_file.stem}_{timestamp}.txt"

    search_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': f"1-{num_to_scan}",
        'search_sort': 'view_count',
        'ignoreerrors': True,
    }
    if date_filter_str:
        search_opts['dateafter'] = date_filter_str

    video_opts = {
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
    }

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("============================================================\n")
        f.write(f"       UNDERDOG SEO REPORT: CHANNELS < {sub_limit:,} SUBS\n")
        f.write(f"       FILTERS: Min {min_views:,} views | Date: {'Since ' + date_filter_str if date_filter_str else 'All Time'}\n")
        f.write("============================================================\n\n")

        for q_idx, query in enumerate(queries, 1):
            print(f"\n🔎 [{q_idx}/{len(queries)}] Scanning: {query}")
            f.write(f"--- SEARCH BATCH {q_idx}: {query} ---\n\n")

            try:
                with yt_dlp.YoutubeDL(search_opts) as ydl:
                    search_url = f"ytsearch{num_to_scan}:{query}"
                    search_result = ydl.extract_info(search_url, download=False)
                    video_entries = search_result.get('entries', [])

                found_count = 0
                for v_idx, entry in enumerate(video_entries, 1):
                    if not entry: continue
                    v_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                    
                    try:
                        with yt_dlp.YoutubeDL(video_opts) as ydl_video:
                            video = ydl_video.extract_info(v_url, download=False)
                            
                            # GATE 1: Date Validation
                            raw_upload_date = video.get('upload_date')
                            if cutoff_date_obj and raw_upload_date:
                                video_date = datetime.strptime(raw_upload_date, '%Y%m%d')
                                if video_date < cutoff_date_obj:
                                    continue

                            # GATE 2: View Count Validation
                            views = video.get('view_count', 0)
                            if views < min_views:
                                continue

                            # GATE 3: Underdog Subscriber Filter
                            sub_count = video.get('channel_follower_count')
                            if sub_count is not None and sub_count < sub_limit:
                                found_count += 1
                                title = video.get('title', 'N/A')
                                channel = video.get('uploader', 'N/A')
                                tags = video.get('tags', [])

                                print(f"   ✨ MATCH: {title[:40]}... ({views:,} views)")

                                f.write(f"MATCH #{found_count} (Rank: {v_idx})\n")
                                f.write(f"CHANNEL: {channel} | SUBS: {sub_count:,}\n")
                                f.write(f"TITLE: {title}\n")
                                f.write(f"VIEWS: {views:,} | DATE: {raw_upload_date}\n")
                                f.write(f"URL: {v_url}\n")
                                f.write(f"TAGS: {', '.join(tags) if tags else 'None'}\n\n")

                    except Exception:
                        continue
                
                if found_count == 0:
                    f.write(f"No underdog channels matching view/date criteria for this query.\n\n")
                
                f.write("-" * 40 + "\n\n")

            except Exception as qe:
                print(f"⚠️ Search failed for query '{query}': {qe}")

    print(f"\n✨ COMPLETE! Results saved to:\n{output_filename}")

if __name__ == "__main__":
    harvest_search_seo_data()