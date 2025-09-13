#!/usr/bin/env python3
"""
Sample Subtitle Creator
Creates sample subtitle files for testing the FFmpeg demo app
"""

import os

def create_sample_srt(filename="sample.srt"):
    """Create a sample SRT subtitle file"""
    srt_content = """1
00:00:00,000 --> 00:00:03,000
Welcome to the FFmpeg Demo Application

2
00:00:03,000 --> 00:00:06,000
This is a sample subtitle file

3
00:00:06,000 --> 00:00:09,000
You can use this to test subtitle features

4
00:00:09,000 --> 00:00:12,000
Try burning subtitles into your videos

5
00:00:12,000 --> 00:00:15,000
Or extract subtitles from existing videos

6
00:00:15,000 --> 00:00:18,000
Convert between different subtitle formats

7
00:00:18,000 --> 00:00:21,000
And much more with FFmpeg!

8
00:00:21,000 --> 00:00:24,000
Enjoy exploring video processing!

9
00:00:24,000 --> 00:00:27,000
This subtitle file was created automatically

10
00:00:27,000 --> 00:00:30,000
For testing purposes only
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    print(f"Sample SRT file created: {filename}")

def create_sample_ass(filename="sample.ass"):
    """Create a sample ASS subtitle file"""
    ass_content = """[Script Info]
Title: FFmpeg Demo Sample
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,Welcome to the FFmpeg Demo Application
Dialogue: 0,0:00:03.00,0:00:06.00,Default,,0,0,0,,This is a sample ASS subtitle file
Dialogue: 0,0:00:06.00,0:00:09.00,Default,,0,0,0,,You can use this to test subtitle features
Dialogue: 0,0:00:09.00,0:00:12.00,Default,,0,0,0,,Try burning subtitles into your videos
Dialogue: 0,0:00:12.00,0:00:15.00,Default,,0,0,0,,Or extract subtitles from existing videos
Dialogue: 0,0:00:15.00,0:00:18.00,Default,,0,0,0,,Convert between different subtitle formats
Dialogue: 0,0:00:18.00,0:00:21.00,Default,,0,0,0,,And much more with FFmpeg!
Dialogue: 0,0:00:21.00,0:00:24.00,Default,,0,0,0,,Enjoy exploring video processing!
Dialogue: 0,0:00:24.00,0:00:27.00,Default,,0,0,0,,This subtitle file was created automatically
Dialogue: 0,0:00:27.00,0:00:30.00,Default,,0,0,0,,For testing purposes only
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    print(f"Sample ASS file created: {filename}")

def create_sample_vtt(filename="sample.vtt"):
    """Create a sample WebVTT subtitle file"""
    vtt_content = """WEBVTT

00:00:00.000 --> 00:00:03.000
Welcome to the FFmpeg Demo Application

00:00:03.000 --> 00:00:06.000
This is a sample WebVTT subtitle file

00:00:06.000 --> 00:00:09.000
You can use this to test subtitle features

00:00:09.000 --> 00:00:12.000
Try burning subtitles into your videos

00:00:12.000 --> 00:00:15.000
Or extract subtitles from existing videos

00:00:15.000 --> 00:00:18.000
Convert between different subtitle formats

00:00:18.000 --> 00:00:21.000
And much more with FFmpeg!

00:00:21.000 --> 00:00:24.000
Enjoy exploring video processing!

00:00:24.000 --> 00:00:27.000
This subtitle file was created automatically

00:00:27.000 --> 00:00:30.000
For testing purposes only
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(vtt_content)
    
    print(f"Sample WebVTT file created: {filename}")

def main():
    """Create sample subtitle files"""
    print("Creating sample subtitle files...")
    
    # Create samples directory
    sample_dir = "samples"
    os.makedirs(sample_dir, exist_ok=True)
    
    # Create different subtitle formats
    create_sample_srt(f"{sample_dir}/sample.srt")
    create_sample_ass(f"{sample_dir}/sample.ass")
    create_sample_vtt(f"{sample_dir}/sample.vtt")
    
    print(f"\nSample subtitle files created in '{sample_dir}' directory:")
    for file in os.listdir(sample_dir):
        if file.endswith(('.srt', '.ass', '.vtt')):
            file_path = os.path.join(sample_dir, file)
            size = os.path.getsize(file_path)
            print(f"  {file} ({size:,} bytes)")
    
    print("\nYou can now use these subtitle files to test the FFmpeg demo application!")

if __name__ == "__main__":
    main()
