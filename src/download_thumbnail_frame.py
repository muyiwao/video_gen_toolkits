import os
import re
import subprocess
import yt_dlp

def extract_and_upscale_thumbnail(video_url, output_dir):
    """
    Extracts the very first frame of a YouTube video using yt-dlp and FFmpeg,
    forcing it into a 4K upscaled 16:9 image wrapper.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize video URL to create a valid filename
    video_id_match = re.search(r'(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/)([^"&?\/\s]+)', video_url)
    video_id = video_id_match.group(1) if video_id_match else "extracted_frame"
    output_filename = f"{video_id}_first_frame_4K.jpg"
    output_path = os.path.join(output_dir, output_filename)

    print(f"\nFetching video streams for: {video_url}")

    # Configure yt-dlp to get the absolute direct URL of the best video stream
    ydl_opts = {
        'format': 'bestvideo',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            stream_url = info['url']
    except Exception as e:
        print(f"Error fetching metadata via yt-dlp: {e}")
        return

    print("Extracting first frame and upscaling to 4K 16:9 via FFmpeg...")

    # FFmpeg complex explanation:
    # 1. scale=3840:2160:force_original_aspect_ratio=increase -> scales up to match 4K bounds while preserving original aspect ratio
    # 2. crop=3840:2160 -> crops out any overflow to clamp the asset strictly into a perfect 16:9 window
    # 3. unsharp -> subtle sharpening pass to clean up native scaling blur artifact blocks
    filter_complex = "scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,unsharp=3:3:0.5:3:3:0.0"

    cmd = [
        'ffmpeg',
        '-ss', '00:00:00.000',          # Seek to the absolute start
        '-i', stream_url,               # Read from direct youtube stream URL
        '-vframes', '1',                # Extract exactly 1 frame
        '-vf', filter_complex,          # Pass our 4K video scale filter
        '-q:v', '2',                    # High-quality JPEG factor (scale from 1-31, lower is better)
        '-y', output_path               # Overwrite existing
    ]

    try:
        # Run FFmpeg silently by redirecting stderr/stdout
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"Success! Saved 4K frame to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed to process video frame: {e}")

def main():
    # PLACEHOLDER: Define your output path folder location here
    OUTPUT_DIRECTORY = r"C:\Project_Works\MuyProjects\video_gen_toolkits\rain_content\recorded\first_processed"

    print("--- YouTube Batch First Frame Grabber (4K 16:9) ---")
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