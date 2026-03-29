import yt_dlp
import os
from pathlib import Path

def download_youtube_content():
    print("--- YouTube Multi-Downloader Tool ---")
    url = input("🔗 Enter YouTube URL: ").strip()
    
    print("\nSelect Download Type:")
    print("1. Video (Highest Quality MP4)")
    print("2. Audio Only (High Quality MP3)")
    print("3. Thumbnail (Image)")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()

    # Define Download Path
    download_path = Path.cwd() / "youtube_downloads"
    download_path.mkdir(exist_ok=True)

    # Base options
    ydl_opts = {
        'outtmpl': str(download_path / '%(title)s.%(ext)s'),
        'noplaylist': True,
    }

    try:
        if choice == '1':
            # Video settings
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })
            print(f"\n🎬 Downloading Video...")
            
        elif choice == '2':
            # Audio settings (Extracts and converts to MP3)
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            print(f"\n🎵 Extracting Audio (MP3)...")

        elif choice == '3':
            # Thumbnail settings
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
            
        print(f"\n✅ Task complete! Files saved in: {download_path}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    download_youtube_content()