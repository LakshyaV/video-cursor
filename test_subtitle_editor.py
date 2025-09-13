#!/usr/bin/env python3
"""
Test script to verify subtitle editor functionality
"""

import tkinter as tk
from ffmpeg_demo import SubtitleEditor

def test_subtitle_editor():
    """Test the subtitle editor independently"""
    root = tk.Tk()
    root.title("Subtitle Editor Test")
    
    # Create a test video path (doesn't need to exist for UI testing)
    test_video = "test_video.mp4"
    test_ffmpeg = "./ffmpeg.exe"
    
    # Create subtitle editor
    editor = SubtitleEditor(root, test_video, test_ffmpeg)
    
    root.mainloop()

if __name__ == "__main__":
    test_subtitle_editor()
