#!/usr/bin/env python3
"""
Sample Media File Creator
Creates sample video and audio files for testing the FFmpeg demo app
"""

from media_utils import create_sample_video, create_sample_audio
from create_sample_subtitle import create_sample_srt, create_sample_ass, create_sample_vtt
import os

def main():
    """Create sample media files for testing"""
    print("Creating sample media files for FFmpeg demo...")
    
    # Create sample directory
    sample_dir = "samples"
    os.makedirs(sample_dir, exist_ok=True)
    
    # Create sample videos with different characteristics
    print("Creating sample videos...")
    create_sample_video(f"{sample_dir}/sample_short.mp4", duration=5, width=640, height=480)
    create_sample_video(f"{sample_dir}/sample_hd.mp4", duration=10, width=1280, height=720)
    create_sample_video(f"{sample_dir}/sample_small.mp4", duration=3, width=320, height=240)
    
    # Create sample audio files
    print("Creating sample audio files...")
    create_sample_audio(f"{sample_dir}/sample_audio_short.wav", duration=5)
    create_sample_audio(f"{sample_dir}/sample_audio_long.wav", duration=15)
    
    # Create sample subtitle files
    print("Creating sample subtitle files...")
    create_sample_srt(f"{sample_dir}/sample.srt")
    create_sample_ass(f"{sample_dir}/sample.ass")
    create_sample_vtt(f"{sample_dir}/sample.vtt")
    
    print(f"\nSample files created in '{sample_dir}' directory:")
    for file in os.listdir(sample_dir):
        file_path = os.path.join(sample_dir, file)
        size = os.path.getsize(file_path)
        print(f"  {file} ({size:,} bytes)")
    
    print("\nYou can now use these files to test the FFmpeg demo application!")

if __name__ == "__main__":
    main()
