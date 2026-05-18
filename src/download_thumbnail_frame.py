import os
import re
import subprocess
import yt_dlp

def extract_and_upscale_thumbnail(video_url, output_dir):
    """
    Fetches the highest-resolution YouTube thumbnail URL using yt-dlp,
    and runs it through FFmpeg to upscale it into a 4K 16:9 image.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize video URL to create a valid filename
    video_id_match = re.search(r'(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/)([^"&?\/\s]+)', video_url)
    video_id = video_id_match.group(1) if video_id_match else "extracted_thumbnail"
    output_filename = f"{video_id}_thumbnail_4K.jpg"
    output_path = os.path.join(output_dir, output_filename)

    print(f"\nFetching thumbnail metadata for: {video_url}")

    # Configure yt-dlp to extract information without downloading video files
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # Pull the absolute best quality thumbnail URL found
            thumbnail_url = info.get('thumbnail')
            
            if not thumbnail_url:
                print("Could not find a valid thumbnail URL for this link.")
                return
    except Exception as e:
        print(f"Error fetching metadata via yt-dlp: {e}")
        return

    print("Upscaling thumbnail image to 4K 16:9 via FFmpeg...")

    # FFmpeg processing chain logic:
    # 1. scale=3840:2160:force_original_aspect_ratio=increase -> Forces asset up to 4K boundaries
    # 2. crop=3840:2160 -> Crops away any potential black bars/letterboxing to maintain a hard 16:9 frame
    # 3. unsharp -> Crisp sharpening mask layer optimization for higher-fidelity upscaling
    filter_complex = "scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,unsharp=3:3:0.5:3:3:0.0"

    cmd = [
        'ffmpeg',
        '-i', thumbnail_url,            # Input direct image thumbnail URL
        '-vf', filter_complex,          # Pass our 4K aspect layout filter chain
        '-q:v', '2',                    # High-quality JPEG factor compression configuration
        '-y', output_path               # Save and overwrite output path
    ]

    try:
        # Run FFmpeg silently by redirecting stderr/stdout
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"Success! Saved 4K Thumbnail to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed to upscale thumbnail image: {e}")

def main():
    # Production Path Output Directory mapping
    OUTPUT_DIRECTORY = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\first_processed"

    print("--- YouTube Batch Thumbnail Grabber & 4K Upscaler (16:9) ---")
    user_input = input("Enter YouTube URLs (separated by spaces or commas):\n").strip()

    if not user_input:
        print("No input provided. Exiting.")
        return

    # Normalize split string handling spaces or commas
    url_list = [url.strip() for url in re.split(r'[\s,]+', user_input) if url.strip()]

    print(f"\nFound {len(url_list)} target links to parse.")
    for idx, url in enumerate(url_list, start=1):
        print(f"\nProcessing job [{idx}/{len(url_list)}]")
        extract_and_upscale_thumbnail(url, OUTPUT_DIRECTORY)

    print("\n--- Batch Run Complete ---")

if __name__ == "__main__":
    main()