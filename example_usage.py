#!/usr/bin/env python3
"""
Example usage of FFmpeg utilities.
"""

from ffmpeg_utils import FFmpegUtils, trim_video, convert_video, add_subtitles

def main():
    # Example 1: Using the class-based approach
    ffmpeg = FFmpegUtils()  # Uses "ffmpeg" from PATH by default
    # Or specify custom path: ffmpeg = FFmpegUtils("/path/to/ffmpeg")
    
    # Trim video from 1 minute to 2 minutes (1 minute duration)
    result = ffmpeg.trim_video(
        input_path="input_video.mp4",
        output_path="trimmed_video.mp4",
        start_time="00:01:00",
        duration="00:01:00",
        precise=True  # Use precise trimming
    )
    
    if result["success"]:
        print("Video trimmed successfully!")
    else:
        print(f"Error: {result['error']}")
    
    # Example 2: Using convenience functions
    # Convert video to different format
    result = convert_video(
        input_path="input_video.mp4",
        output_path="converted_video.avi",
        video_codec="libx264",
        quality="18"  # Higher quality
    )
    
    # Example 3: Add subtitles
    result = add_subtitles(
        input_path="input_video.mp4",
        output_path="video_with_subs.mp4",
        subtitle_path="subtitles.srt",
        burn=True  # Burn subtitles into video
    )
    
    # Example 4: Apply video effects
    result = ffmpeg.apply_video_effects(
        input_path="input_video.mp4",
        output_path="video_with_effects.mp4",
        blur=2,
        brightness=0.1,
        contrast=1.2,
        artistic_filter="vintage"
    )
    
    # Example 5: Add background music
    result = ffmpeg.add_background_music(
        input_path="input_video.mp4",
        output_path="video_with_music.mp4",
        music_path="background_music.mp3",
        volume=0.3,  # 30% volume
        mix=True  # Mix with original audio
    )
    
    # Example 6: Get media information
    result = ffmpeg.get_media_info("input_video.mp4")
    if result["success"]:
        info = result["info"]
        print(f"Duration: {info['format']['duration']} seconds")
        print(f"Size: {info['format']['size']} bytes")
        for stream in info['streams']:
            if stream['codec_type'] == 'video':
                print(f"Video: {stream['width']}x{stream['height']} {stream['codec_name']}")
            elif stream['codec_type'] == 'audio':
                print(f"Audio: {stream['codec_name']} {stream['sample_rate']}Hz")

if __name__ == "__main__":
    main()
