import yt_dlp
import os
import re
from pathlib import Path

def download_youtube_content():
    print("--- YouTube Multi-Downloader Tool ---")
    
    # 1. Collect URLs
    raw_urls = input("🔗 Enter YouTube URL(s) [Separate by commas or spaces]: ").strip()
    # Split by comma or space and filter out empty strings
    urls = [u.strip() for u in re.split(r'[,\s]+', raw_urls) if u.strip()]
    
    if not urls:
        print("❌ No URLs provided.")
        return

    print(f"\nDetected {len(urls)} link(s).")
    
    print("\nSelect Download Type:")
    print("1. Video WITH Audio (Highest Quality MP4)")
    print("2. Video ONLY (Silent - No Audio)")
    print("3. Audio ONLY (High Quality MP3)")
    print("4. Thumbnail (Image)")
    
    choice = input("\nEnter choice (1, 2, 3, or 4): ").strip()

    # Define Download Path
    download_path = Path(r"C:\Project_Works\MuyProjects\video_gen_toolkits\yt_utils\yt_dls")
    download_path.mkdir(parents=True, exist_ok=True)

    # --- Process Each URL ---
    for index, url in enumerate(urls, 1):
        print(f"\n{'='*40}")
        print(f"Processing ({index}/{len(urls)}): {url}")
        
        is_cut = False
        start_ts = None
        end_ts = None

        # Scope Selection (Asked per video if multiple links, as cuts are usually unique)
        if choice in ['1', '2', '3']:
            print(f"\nSelect Scope for this specific video:")
            print("A. Full Video")
            print("B. Specific Cut (Timestamp)")
            scope = input("Enter choice (A or B): ").strip().upper()
            
            if scope == 'B':
                is_cut = True
                start_ts = input("   Enter Start Timestamp (e.g., 00:00:10): ").strip()
                end_ts = input("   Enter End Timestamp (e.g., 00:00:20): ").strip()

        # Reset options for each download
        ydl_opts = {
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
        }

        # Cutting Logic
        if is_cut:
            ydl_opts.update({
                'external_downloader': 'ffmpeg',
                'external_downloader_args': {
                    'ffmpeg_i': ['-ss', start_ts, '-to', end_ts]
                },
                'force_keyframes_at_cuts': True, 
            })

        try:
            if choice == '1':
                ydl_opts['outtmpl'] = str(download_path / '%(title).80s_full.%(ext)s')
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'merge_output_format': 'mp4',
                })
                
            elif choice == '2':
                ydl_opts['outtmpl'] = str(download_path / '%(title).80s_silent.%(ext)s')
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]/bestvideo',
                    'merge_output_format': 'mp4',
                })

            elif choice == '3':
                ydl_opts['outtmpl'] = str(download_path / '%(title).80s_audio.%(ext)s')
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })

            elif choice == '4':
                ydl_opts['outtmpl'] = str(download_path / '%(title).80s_thumb.%(ext)s')
                ydl_opts.update({
                    'skip_download': True,
                    'writethumbnail': True,
                })

            else:
                print("❌ Invalid selection. Skipping...")
                continue

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            print(f"✅ Finished: {url}")

        except Exception as e:
            print(f"❌ Error processing {url}: {e}")

    print(f"\n--- ALL TASKS COMPLETE ---")
    print(f"Files saved to: {download_path}")

if __name__ == "__main__":
    download_youtube_content()