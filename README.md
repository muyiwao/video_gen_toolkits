## Project Structure

```text
VIDEO_GEN_TOOLKITS/
├── grok_script/
│   ├── movie\series_1\episode_1\output/
│   │   └── final_merged_video.mp4
│   ├── get_last_frame.py
│   ├── grok_create_rename.py
│   └── grok_move_delete_file.py
├── muyverse_maths/
│   ├── processed/
│   └── scripts/
│       ├── create_maths_long_video.py
│       └── mathgpt_move_rename.py
├── rain_content/
│   ├── recorded/
│   │   ├── curated/
│   │   ├── processed/
│   │   └── raw/
│   └── scripts/
│       ├── create_ultra_long_rain_loop.py
│       ├── enhance_rain_image.py
│       ├── enhance_rain_video.py
│       └── vertical_rain_loop.py
├── .gitignore
├── extract_frame_interval_2k.py
├── merge_videos.py
└── upscaling_video.py