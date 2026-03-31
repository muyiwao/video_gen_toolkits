import yt_dlp
from datetime import datetime
from pathlib import Path

def extract_channel_data_to_file():
    """
    Prompts for a YouTube Channel URL and extracts all public playlists 
    and their video titles into a structured text file.
    """
    # 1. User Input
    print("\n--- YouTube Playlist Content Extractor ---")
    channel_input = input("🔗 Enter YouTube Channel URL or @Handle: ").strip()
    
    if not channel_input:
        print("❌ No input detected. Exiting.")
        return

    # 2. URL Sanitization
    # Ensures handles like '@muyversemaths' become full URLs
    if channel_input.startswith("@"):
        channel_url = f"https://www.youtube.com/{channel_input}/playlists"
    elif "youtube.com" in channel_input and "/playlists" not in channel_input:
        channel_url = channel_input.rstrip('/') + "/playlists"
    else:
        channel_url = channel_input

    # 3. yt-dlp Configuration
    ydl_opts = {
        'extract_flat': True, 
        'quiet': True,
        'no_warnings': True,
        'force_generic_extract': False,
    }

    output_filename = "youtube_playlists_export.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n⏳ Accessing YouTube data for: {channel_url}...")
            
            # Extract the high-level channel/playlist tab data
            channel_info = ydl.extract_info(channel_url, download=False)
            playlists = channel_info.get('entries', [])

            if not playlists:
                print("⚠️ No playlists found. If the channel has playlists, try updating yt-dlp: 'pip install -U yt-dlp'")
                return

            # 4. File Writing Logic
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(f"YOUTUBE PLAYLIST CONTENT EXPORT\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Target Source: {channel_url}\n")
                f.write("="*60 + "\n\n")

                print(f"📂 Found {len(playlists)} playlists. Processing titles...")

                for p_idx, playlist in enumerate(playlists, 1):
                    p_title = playlist.get('title', 'Untitled')
                    p_url = playlist.get('url') or playlist.get('webpage_url')
                    
                    print(f"   > Processing: {p_title}")
                    f.write(f"PLAYLIST {p_idx}: {p_title}\nURL: {p_url}\n" + "-"*30 + "\n")

                    try:
                        # Extract videos inside this specific playlist
                        # We use a separate internal call to avoid flat-extraction conflicts
                        playlist_data = ydl.extract_info(p_url, download=False)
                        videos = playlist_data.get('entries', [])
                        
                        if not videos:
                            f.write("   (Empty or Private Playlist)\n")
                        else:
                            for v_idx, video in enumerate(videos, 1):
                                v_title = video.get('title', 'Unknown Title')
                                f.write(f"   {v_idx}. {v_title}\n")
                    except Exception as e:
                        f.write(f"   [Error accessing playlist entries: {str(e)}]\n")
                    
                    f.write("\n")

            print(f"\n✨ SUCCESS! Data saved to: {Path(output_filename).absolute()}")

    except Exception as e:
        print(f"\n❌ Critical Error: {e}")

if __name__ == "__main__":
    extract_channel_data_to_file()