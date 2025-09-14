#!/usr/bin/env python3
"""
Output utilities for working with generated video files.
"""

import os
import subprocess
import webbrowser
from pathlib import Path


def open_video_file(file_path):
    """
    Open a video file with the default system video player.
    
    Args:
        file_path (str): Path to the video file
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Try to open with default application
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # macOS and Linux
            subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', file_path])
        else:
            print("❌ Unsupported operating system")
            return False
        
        print(f"✅ Opening video: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error opening video: {e}")
        return False


def open_file_location(file_path):
    """
    Open the file location in the system file explorer.
    
    Args:
        file_path (str): Path to the file
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        directory = os.path.dirname(os.path.abspath(file_path))
        
        if os.name == 'nt':  # Windows
            subprocess.run(['explorer', '/select,', os.path.abspath(file_path)])
        elif os.name == 'posix':  # macOS and Linux
            if os.uname().sysname == 'Darwin':  # macOS
                subprocess.run(['open', '-R', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', directory])
        else:
            print("❌ Unsupported operating system")
            return False
        
        print(f"✅ Opening file location: {directory}")
        return True
    except Exception as e:
        print(f"❌ Error opening file location: {e}")
        return False


def get_file_info(file_path):
    """
    Get detailed information about a video file.
    
    Args:
        file_path (str): Path to the video file
        
    Returns:
        dict: File information
    """
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    try:
        stat = os.stat(file_path)
        return {
            "path": os.path.abspath(file_path),
            "name": os.path.basename(file_path),
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": os.path.splitext(file_path)[1]
        }
    except Exception as e:
        return {"error": str(e)}


def list_output_files(directory="."):
    """
    List all video files in a directory.
    
    Args:
        directory (str): Directory to search in
        
    Returns:
        list: List of video file paths
    """
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    video_files = []
    
    try:
        for file in os.listdir(directory):
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(directory, file))
        
        return sorted(video_files)
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []


def copy_to_desktop(file_path, new_name=None):
    """
    Copy a video file to the desktop.
    
    Args:
        file_path (str): Path to the source file
        new_name (str): New name for the file (optional)
        
    Returns:
        str: Path to the copied file, or None if failed
    """
    if not os.path.exists(file_path):
        print(f"❌ Source file not found: {file_path}")
        return None
    
    try:
        # Get desktop path
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # Create new filename
        if new_name:
            filename = new_name
            if not filename.endswith('.mp4'):
                filename += '.mp4'
        else:
            filename = os.path.basename(file_path)
        
        dest_path = os.path.join(desktop, filename)
        
        # Copy file
        import shutil
        shutil.copy2(file_path, dest_path)
        
        print(f"✅ Copied to desktop: {dest_path}")
        return dest_path
    except Exception as e:
        print(f"❌ Error copying file: {e}")
        return None


def main():
    """Example usage of output utilities."""
    print("🎬 Video Output Utilities")
    print("=" * 30)
    
    # List all video files in current directory
    video_files = list_output_files()
    
    if video_files:
        print("📁 Found video files:")
        for i, file_path in enumerate(video_files, 1):
            info = get_file_info(file_path)
            if "error" not in info:
                print(f"  {i}. {info['name']} ({info['size_mb']:.2f} MB)")
        
        print("\n💡 You can use these functions:")
        print("  - open_video_file('path/to/video.mp4')  # Play video")
        print("  - open_file_location('path/to/video.mp4')  # Show in explorer")
        print("  - copy_to_desktop('path/to/video.mp4')  # Copy to desktop")
    else:
        print("📁 No video files found in current directory")


if __name__ == "__main__":
    main()
