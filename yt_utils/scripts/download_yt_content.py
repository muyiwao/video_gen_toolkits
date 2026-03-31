import yt_dlp
import os
import re
from pathlib import Path

def download_youtube_content():
    print("--- YouTube Multi-Downloader Tool ---")
    url = input("🔗 Enter YouTube URL: ").strip()
    
    print("\nSelect Download Type:")
    print("1. Video WITH Audio (Highest Quality MP4)")
    print("2. Video ONLY (Silent - No Audio)")
    print("3. Audio ONLY (High Quality MP3)")
    print("4. Thumbnail (Image)")
    
    choice = input("\nEnter choice (1, 2, 3, or 4): ").strip()

    # --- Download Scope Selection ---
    is_cut = False
    start_ts = None
    end_ts = None

    if choice in ['1', '2', '3']:
        print("\nSelect Download Scope:")
        print("A. Full Video")
        print("B. Specific Cut (Timestamp)")
        scope = input("Enter choice (A or B): ").strip().upper()
        
        if scope == 'B':
            is_cut = True
            start_ts = input("   Enter Start Timestamp (e.g., 00:05:12): ").strip()
            end_ts = input("   Enter End Timestamp (e.g., 00:05:46): ").strip()

    # Define Download Path
    download_path = Path(r"C:\Project_Works\YouTubeVideos\video_gen_toolkits\yt_utils\yt_dls")
    download_path.mkdir(parents=True, exist_ok=True)

    # Base options
    ydl_opts = {
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
    }

    # --- Precise Cutting Logic ---
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
            # VIDEO WITH AUDIO
            ydl_opts['outtmpl'] = str(download_path / '%(title).80s_full.%(ext)s')
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            })
            print(f"\n🎬 Downloading Video + Audio...")
            
        elif choice == '2':
            # VIDEO ONLY (SILENT)
            ydl_opts['outtmpl'] = str(download_path / '%(title).80s_silent.%(ext)s')
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]/bestvideo',
                'merge_output_format': 'mp4',
            })
            print(f"\n🔇 Downloading Silent Video...")

        elif choice == '3':
            # AUDIO ONLY (MP3)
            ydl_opts['outtmpl'] = str(download_path / '%(title).80s_audio.%(ext)s')
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            print(f"\n🎵 Extracting Audio (MP3)...")

        elif choice == '4':
            # THUMBNAIL
            ydl_opts['outtmpl'] = str(download_path / '%(title).80s_thumb.%(ext)s')
            ydl_opts.update({
                'skip_download': True,
                'writethumbnail': True,
            })
            print(f"\n🖼️ Downloading Thumbnail...")

        else:
            print("❌ Invalid selection.")
            return

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        print(f"\n✅ Task complete! Check folder: {download_path}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    download_youtube_content()