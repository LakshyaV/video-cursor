#!/usr/bin/env python3
"""
FFmpeg Installer for Windows
Downloads and sets up FFmpeg for the demo application
"""

import os
import sys
import subprocess
import zipfile
import requests
from pathlib import Path

def download_file(url, filename):
    """Download a file from URL"""
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded {filename}")

def install_ffmpeg():
    """Install FFmpeg for Windows"""
    print("Installing FFmpeg for Windows...")
    
    # Create ffmpeg directory
    ffmpeg_dir = Path("ffmpeg")
    ffmpeg_dir.mkdir(exist_ok=True)
    
    # Download FFmpeg (using a direct link to a recent build)
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    zip_filename = "ffmpeg.zip"
    
    try:
        download_file(ffmpeg_url, zip_filename)
        
        # Extract the zip file
        print("Extracting FFmpeg...")
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_dir)
        
        # Find the extracted folder
        extracted_folders = [f for f in ffmpeg_dir.iterdir() if f.is_dir()]
        if extracted_folders:
            ffmpeg_bin_dir = extracted_folders[0] / "bin"
            if ffmpeg_bin_dir.exists():
                # Copy ffmpeg.exe to the project directory
                import shutil
                shutil.copy2(ffmpeg_bin_dir / "ffmpeg.exe", "ffmpeg.exe")
                shutil.copy2(ffmpeg_bin_dir / "ffprobe.exe", "ffprobe.exe")
                print("FFmpeg installed successfully!")
                
                # Clean up
                os.remove(zip_filename)
                import shutil
                shutil.rmtree(ffmpeg_dir)
                
                return True
            else:
                print("Error: Could not find FFmpeg binary directory")
                return False
        else:
            print("Error: Could not extract FFmpeg")
            return False
            
    except Exception as e:
        print(f"Error installing FFmpeg: {e}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is working"""
    try:
        result = subprocess.run(['./ffmpeg.exe', '-version'], 
                              capture_output=True, text=True, check=True)
        print("FFmpeg is working!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg is not working")
        return False

def main():
    """Main installation function"""
    print("FFmpeg Installer for Windows")
    print("=" * 30)
    
    # Check if FFmpeg is already working
    if check_ffmpeg():
        print("FFmpeg is already installed and working!")
        return
    
    # Install FFmpeg
    if install_ffmpeg():
        print("\nFFmpeg installation completed!")
        print("You can now run the demo application.")
    else:
        print("\nFFmpeg installation failed.")
        print("Please install FFmpeg manually from https://ffmpeg.org/download.html")

if __name__ == "__main__":
    main()
