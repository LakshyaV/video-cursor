#!/usr/bin/env python3
"""
Media Utilities for FFmpeg Demo
Helper functions for creating sample media files and advanced processing
"""

import cv2
import numpy as np
import os
import subprocess
from pathlib import Path

def create_sample_video(output_path="sample_video.mp4", duration=10, width=640, height=480):
    """Create a sample video file for testing"""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
    
    for i in range(duration * 30):  # 30 FPS
        # Create a frame with moving gradient
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create gradient background
        for y in range(height):
            for x in range(width):
                frame[y, x] = [
                    int(255 * (x / width)),  # Red gradient
                    int(255 * (y / height)),  # Green gradient
                    int(255 * ((x + y) / (width + height)))  # Blue gradient
                ]
        
        # Add moving circle
        center_x = int(width / 2 + 100 * np.sin(i * 0.1))
        center_y = int(height / 2 + 50 * np.cos(i * 0.1))
        cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), -1)
        
        # Add text
        text = f"Frame {i+1}"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        out.write(frame)
    
    out.release()
    print(f"Sample video created: {output_path}")

def create_sample_audio(output_path="sample_audio.wav", duration=10, sample_rate=44100):
    """Create a sample audio file for testing"""
    # Generate a simple sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    frequency = 440  # A4 note
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Write WAV file
    import wave
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"Sample audio created: {output_path}")

def merge_videos(video_files, output_path="merged_video.mp4"):
    """Merge multiple video files"""
    if len(video_files) < 2:
        raise ValueError("Need at least 2 video files to merge")
    
    # Create file list for FFmpeg
    file_list_path = "file_list.txt"
    with open(file_list_path, 'w') as f:
        for video_file in video_files:
            f.write(f"file '{video_file}'\n")
    
    command = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', file_list_path,
        '-c', 'copy', '-y', output_path
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Videos merged successfully: {output_path}")
    finally:
        # Clean up file list
        if os.path.exists(file_list_path):
            os.remove(file_list_path)

def add_watermark(input_video, watermark_text, output_video="watermarked_video.mp4"):
    """Add text watermark to video"""
    command = [
        'ffmpeg', '-i', input_video,
        '-vf', f"drawtext=text='{watermark_text}':fontsize=24:fontcolor=white:x=10:y=10",
        '-c:a', 'copy', '-y', output_video
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Watermark added: {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"Error adding watermark: {e}")

def extract_frames(input_video, output_dir="frames", frame_rate=1):
    """Extract frames from video at specified frame rate"""
    os.makedirs(output_dir, exist_ok=True)
    
    command = [
        'ffmpeg', '-i', input_video,
        '-vf', f'fps={frame_rate}',
        f'{output_dir}/frame_%04d.png',
        '-y'
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Frames extracted to: {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting frames: {e}")

def create_slideshow(images_dir, output_video="slideshow.mp4", duration_per_image=3):
    """Create video slideshow from images"""
    command = [
        'ffmpeg', '-framerate', str(1/duration_per_image),
        '-pattern_type', 'glob', '-i', f'{images_dir}/*.jpg',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-y', output_video
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Slideshow created: {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating slideshow: {e}")

def get_video_duration(video_path):
    """Get video duration in seconds"""
    command = [
        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', video_path
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None

def resize_video(input_video, output_video, width, height):
    """Resize video to specified dimensions"""
    command = [
        'ffmpeg', '-i', input_video,
        '-vf', f'scale={width}:{height}',
        '-c:a', 'copy', '-y', output_video
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Video resized: {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"Error resizing video: {e}")

def convert_to_webm(input_video, output_video="output.webm", quality="good"):
    """Convert video to WebM format"""
    quality_map = {
        "best": "0",
        "good": "5",
        "fast": "10"
    }
    
    crf = quality_map.get(quality, "5")
    
    command = [
        'ffmpeg', '-i', input_video,
        '-c:v', 'libvpx-vp9', '-crf', crf, '-b:v', '0',
        '-c:a', 'libopus', '-y', output_video
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Video converted to WebM: {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting to WebM: {e}")

if __name__ == "__main__":
    # Create sample files for testing
    print("Creating sample media files...")
    create_sample_video("sample_video.mp4", duration=5)
    create_sample_audio("sample_audio.wav", duration=5)
    print("Sample files created successfully!")
