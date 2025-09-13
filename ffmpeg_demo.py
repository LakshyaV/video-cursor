#!/usr/bin/env python3
"""
FFmpeg Demo Application
A comprehensive GUI application showcasing various FFmpeg capabilities
including video conversion, trimming, merging, and audio processing.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
from pathlib import Path
import ffmpeg
import cv2
from PIL import Image, ImageTk
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import numpy as np

class FFmpegDemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FFmpeg Demo Application")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2c3e50')
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.start_time = tk.StringVar(value="00:00:00")
        self.duration = tk.StringVar(value="00:00:10")
        self.quality = tk.StringVar(value="23")
        self.scale_width = tk.StringVar(value="1280")
        self.scale_height = tk.StringVar(value="720")
        
        self.setup_ui()
        self.check_ffmpeg()
        
    def setup_ui(self):
        """Setup the user interface with scrollable canvas"""
        # Create main container frame
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(container, bg='#2c3e50')
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.bind_mousewheel()
        
        # Main frame inside scrollable area
        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="FFmpeg Demo Application", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        self.create_file_section(main_frame, 1)
        
        # Video processing section
        self.create_video_section(main_frame, 2)
        
        # Audio processing section
        self.create_audio_section(main_frame, 3)
        
        # Effects and filters section
        self.create_effects_section(main_frame, 4)
        
        # Advanced options section
        self.create_advanced_section(main_frame, 5)
        
        # Control buttons
        self.create_control_buttons(main_frame, 6)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", foreground='green')
        self.status_label.grid(row=8, column=0, columnspan=3, pady=5)
    
    def bind_mousewheel(self):
        """Bind mousewheel events to canvas for scrolling"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Bind keyboard scrolling
        self.canvas.bind('<Up>', lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind('<Down>', lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind('<Prior>', lambda e: self.canvas.yview_scroll(-1, "pages"))  # Page Up
        self.canvas.bind('<Next>', lambda e: self.canvas.yview_scroll(1, "pages"))    # Page Down
        self.canvas.bind('<Home>', lambda e: self.canvas.yview_moveto(0))
        self.canvas.bind('<End>', lambda e: self.canvas.yview_moveto(1))
        
        # Make canvas focusable for keyboard events
        self.canvas.focus_set()
    
    def update_scroll_region(self):
        """Update the scroll region when content changes"""
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def create_file_section(self, parent, row):
        """Create file selection section"""
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="10")
        file_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(1, weight=1)
        
        # Input file
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_input_file).grid(row=0, column=2, padx=5)
        
        # Output file
        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.output_file, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_output_file).grid(row=1, column=2, padx=5)
        
    def create_video_section(self, parent, row):
        """Create video processing section"""
        video_frame = ttk.LabelFrame(parent, text="Video Processing", padding="10")
        video_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        video_frame.columnconfigure(1, weight=1)
        
        # Video format conversion
        ttk.Label(video_frame, text="Convert Format:").grid(row=0, column=0, sticky=tk.W, pady=2)
        format_var = tk.StringVar(value="mp4")
        format_combo = ttk.Combobox(video_frame, textvariable=format_var, 
                                   values=["mp4", "avi", "mov", "mkv", "webm", "gif"])
        format_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Trim video
        ttk.Label(video_frame, text="Start Time (HH:MM:SS):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(video_frame, textvariable=self.start_time, width=15).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(video_frame, text="Duration (HH:MM:SS):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(video_frame, textvariable=self.duration, width=15).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Video scaling
        ttk.Label(video_frame, text="Scale to:").grid(row=3, column=0, sticky=tk.W, pady=2)
        scale_frame = ttk.Frame(video_frame)
        scale_frame.grid(row=3, column=1, sticky=tk.W, padx=5)
        ttk.Entry(scale_frame, textvariable=self.scale_width, width=8).grid(row=0, column=0)
        ttk.Label(scale_frame, text="x").grid(row=0, column=1, padx=2)
        ttk.Entry(scale_frame, textvariable=self.scale_height, width=8).grid(row=0, column=2)
        
        # Precise trimming option
        self.precise_trim = tk.BooleanVar()
        ttk.Checkbutton(video_frame, text="Precise Trim (re-encodes for accuracy)", 
                       variable=self.precise_trim).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Ultra precise trimming option
        self.ultra_precise = tk.BooleanVar()
        ttk.Checkbutton(video_frame, text="Ultra Precise (2-pass trimming)", 
                       variable=self.ultra_precise).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Quality
        ttk.Label(video_frame, text="Quality (CRF 0-51):").grid(row=6, column=0, sticky=tk.W, pady=2)
        quality_scale = ttk.Scale(video_frame, from_=0, to=51, variable=self.quality, orient=tk.HORIZONTAL)
        quality_scale.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5)
        
    def create_audio_section(self, parent, row):
        """Create audio processing section"""
        audio_frame = ttk.LabelFrame(parent, text="Audio Processing", padding="10")
        audio_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        audio_frame.columnconfigure(1, weight=1)
        
        # Audio codec
        ttk.Label(audio_frame, text="Audio Codec:").grid(row=0, column=0, sticky=tk.W, pady=2)
        audio_codec_var = tk.StringVar(value="aac")
        audio_combo = ttk.Combobox(audio_frame, textvariable=audio_codec_var, 
                                  values=["aac", "mp3", "ac3", "flac", "wav"])
        audio_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Audio bitrate
        ttk.Label(audio_frame, text="Audio Bitrate:").grid(row=1, column=0, sticky=tk.W, pady=2)
        bitrate_var = tk.StringVar(value="128k")
        bitrate_combo = ttk.Combobox(audio_frame, textvariable=bitrate_var, 
                                    values=["64k", "128k", "192k", "256k", "320k"])
        bitrate_combo.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Sound effects section
        effects_frame = ttk.LabelFrame(audio_frame, text="Sound Effects", padding="5")
        effects_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Background music
        ttk.Label(effects_frame, text="Background Music:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.bg_music_file = tk.StringVar()
        music_frame = ttk.Frame(effects_frame)
        music_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        music_frame.columnconfigure(0, weight=1)
        ttk.Entry(music_frame, textvariable=self.bg_music_file, width=30).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(music_frame, text="Browse", command=self.browse_bg_music).grid(row=0, column=1, padx=5)
        
        # Sound effect
        ttk.Label(effects_frame, text="Sound Effect:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sound_effect_file = tk.StringVar()
        effect_frame = ttk.Frame(effects_frame)
        effect_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        effect_frame.columnconfigure(0, weight=1)
        ttk.Entry(effect_frame, textvariable=self.sound_effect_file, width=30).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(effect_frame, text="Browse", command=self.browse_sound_effect).grid(row=0, column=1, padx=5)
        
        # Audio mixing options
        self.mix_audio = tk.BooleanVar()
        ttk.Checkbutton(effects_frame, text="Mix with original audio", 
                       variable=self.mix_audio).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.replace_audio = tk.BooleanVar()
        ttk.Checkbutton(effects_frame, text="Replace original audio", 
                       variable=self.replace_audio).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Volume controls
        ttk.Label(effects_frame, text="Background Volume:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.bg_volume = tk.StringVar(value="0.5")
        ttk.Scale(effects_frame, from_=0, to=2, variable=self.bg_volume, orient=tk.HORIZONTAL).grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(effects_frame, text="Effect Volume:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.effect_volume = tk.StringVar(value="1.0")
        ttk.Scale(effects_frame, from_=0, to=2, variable=self.effect_volume, orient=tk.HORIZONTAL).grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Sound effect timing controls
        ttk.Label(effects_frame, text="Start Time (s):").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.effect_start_time = tk.StringVar(value="0")
        ttk.Entry(effects_frame, textvariable=self.effect_start_time, width=10).grid(row=6, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(effects_frame, text="Duration (s):").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.effect_duration = tk.StringVar(value="")
        ttk.Entry(effects_frame, textvariable=self.effect_duration, width=10).grid(row=7, column=1, sticky=tk.W, padx=5)
        
        self.loop_effect = tk.BooleanVar()
        ttk.Checkbutton(effects_frame, text="Loop Effect", 
                       variable=self.loop_effect).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    def create_effects_section(self, parent, row):
        """Create video effects and filters section"""
        effects_frame = ttk.LabelFrame(parent, text="Video Effects & Filters", padding="10")
        effects_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        effects_frame.columnconfigure(1, weight=1)
        
        # Basic Effects
        basic_frame = ttk.LabelFrame(effects_frame, text="Basic Effects", padding="5")
        basic_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Blur effect
        ttk.Label(basic_frame, text="Blur:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.blur_strength = tk.StringVar(value="0")
        blur_scale = ttk.Scale(basic_frame, from_=0, to=10, variable=self.blur_strength, orient=tk.HORIZONTAL)
        blur_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Brightness
        ttk.Label(basic_frame, text="Brightness:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.brightness = tk.StringVar(value="0")
        brightness_scale = ttk.Scale(basic_frame, from_=-1, to=1, variable=self.brightness, orient=tk.HORIZONTAL)
        brightness_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Contrast
        ttk.Label(basic_frame, text="Contrast:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.contrast = tk.StringVar(value="1")
        contrast_scale = ttk.Scale(basic_frame, from_=0, to=2, variable=self.contrast, orient=tk.HORIZONTAL)
        contrast_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Saturation
        ttk.Label(basic_frame, text="Saturation:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.saturation = tk.StringVar(value="1")
        saturation_scale = ttk.Scale(basic_frame, from_=0, to=2, variable=self.saturation, orient=tk.HORIZONTAL)
        saturation_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Artistic Filters
        artistic_frame = ttk.LabelFrame(effects_frame, text="Artistic Filters", padding="5")
        artistic_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Filter selection
        ttk.Label(artistic_frame, text="Filter:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.artistic_filter = tk.StringVar(value="none")
        filter_combo = ttk.Combobox(artistic_frame, textvariable=self.artistic_filter, width=15)
        filter_combo['values'] = ("none", "black & white", "sepia", "vintage", "negative", "emboss", "edge detection")
        filter_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Motion Effects
        motion_frame = ttk.LabelFrame(effects_frame, text="Motion Effects", padding="5")
        motion_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Zoom effect
        self.zoom_effect = tk.BooleanVar()
        ttk.Checkbutton(motion_frame, text="Zoom In Effect", 
                       variable=self.zoom_effect).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Rotation
        ttk.Label(motion_frame, text="Rotation (degrees):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.rotation = tk.StringVar(value="0")
        rotation_scale = ttk.Scale(motion_frame, from_=-180, to=180, variable=self.rotation, orient=tk.HORIZONTAL)
        rotation_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Mirror effects
        self.horizontal_flip = tk.BooleanVar()
        ttk.Checkbutton(motion_frame, text="Horizontal Flip", 
                       variable=self.horizontal_flip).grid(row=2, column=0, sticky=tk.W, pady=2)
        
        self.vertical_flip = tk.BooleanVar()
        ttk.Checkbutton(motion_frame, text="Vertical Flip", 
                       variable=self.vertical_flip).grid(row=2, column=1, sticky=tk.W, pady=2)
        
    def create_advanced_section(self, parent, row):
        """Create advanced options section"""
        advanced_frame = ttk.LabelFrame(parent, text="Advanced Options", padding="10")
        advanced_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        advanced_frame.columnconfigure(1, weight=1)
        
        # Video codec
        ttk.Label(advanced_frame, text="Video Codec:").grid(row=0, column=0, sticky=tk.W, pady=2)
        video_codec_var = tk.StringVar(value="libx264")
        video_codec_combo = ttk.Combobox(advanced_frame, textvariable=video_codec_var, 
                                        values=["libx264", "libx265", "libvpx", "libvpx-vp9"])
        video_codec_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Additional filters
        ttk.Label(advanced_frame, text="Additional Filters:").grid(row=1, column=0, sticky=tk.W, pady=2)
        filters_var = tk.StringVar()
        ttk.Entry(advanced_frame, textvariable=filters_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Subtitle options
        ttk.Label(advanced_frame, text="Subtitle File:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.subtitle_file = tk.StringVar()
        subtitle_frame = ttk.Frame(advanced_frame)
        subtitle_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        subtitle_frame.columnconfigure(0, weight=1)
        ttk.Entry(subtitle_frame, textvariable=self.subtitle_file, width=30).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(subtitle_frame, text="Browse", command=self.browse_subtitle_file).grid(row=0, column=1, padx=5)
        
        # Subtitle options
        self.burn_subtitles = tk.BooleanVar()
        ttk.Checkbutton(advanced_frame, text="Burn Subtitles into Video", 
                       variable=self.burn_subtitles).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.extract_subtitles = tk.BooleanVar()
        ttk.Checkbutton(advanced_frame, text="Extract Subtitles from Video", 
                       variable=self.extract_subtitles).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
    def create_control_buttons(self, parent, row):
        """Create control buttons"""
        # Main button frame
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # First row of buttons
        first_row = ttk.Frame(button_frame)
        first_row.pack(fill=tk.X, pady=2)
        
        ttk.Button(first_row, text="Convert Video", command=self.convert_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(first_row, text="Trim Video", command=self.trim_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(first_row, text="Extract Audio", command=self.extract_audio).pack(side=tk.LEFT, padx=5)
        ttk.Button(first_row, text="Create GIF", command=self.create_gif).pack(side=tk.LEFT, padx=5)
        ttk.Button(first_row, text="Get Info", command=self.get_media_info).pack(side=tk.LEFT, padx=5)
        
        # Second row of subtitle buttons
        second_row = ttk.Frame(button_frame)
        second_row.pack(fill=tk.X, pady=2)
        
        ttk.Button(second_row, text="Add Subtitles", command=self.add_subtitles).pack(side=tk.LEFT, padx=5)
        ttk.Button(second_row, text="Burn Subtitles", command=self.burn_subtitles_to_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(second_row, text="Extract Subtitles", command=self.extract_subtitles_from_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(second_row, text="Convert Subtitles", command=self.convert_subtitles).pack(side=tk.LEFT, padx=5)
        ttk.Button(second_row, text="Transcribe Audio", command=self.transcribe_audio).pack(side=tk.LEFT, padx=5)
        ttk.Button(second_row, text="Subtitle Editor", command=self.open_subtitle_editor).pack(side=tk.LEFT, padx=5)
        
        # Third row of audio effect buttons
        third_row = ttk.Frame(button_frame)
        third_row.pack(fill=tk.X, pady=2)
        
        ttk.Button(third_row, text="Add Background Music", command=self.add_background_music).pack(side=tk.LEFT, padx=5)
        ttk.Button(third_row, text="Add Sound Effect", command=self.add_sound_effect).pack(side=tk.LEFT, padx=5)
        ttk.Button(third_row, text="Audio Mixer", command=self.open_audio_mixer).pack(side=tk.LEFT, padx=5)
        ttk.Button(third_row, text="Fade In/Out", command=self.add_fade_effects).pack(side=tk.LEFT, padx=5)
        ttk.Button(third_row, text="Audio Normalize", command=self.normalize_audio).pack(side=tk.LEFT, padx=5)
        
        # Fourth row of video effects buttons
        fourth_row = ttk.Frame(button_frame)
        fourth_row.pack(fill=tk.X, pady=2)
        
        ttk.Button(fourth_row, text="Apply Effects", command=self.apply_video_effects).pack(side=tk.LEFT, padx=5)
        ttk.Button(fourth_row, text="Preview Effects", command=self.preview_effects).pack(side=tk.LEFT, padx=5)
        ttk.Button(fourth_row, text="Reset Effects", command=self.reset_effects).pack(side=tk.LEFT, padx=5)
        
    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        # Check for local FFmpeg first, then system PATH
        ffmpeg_paths = ['./ffmpeg.exe', 'ffmpeg']
        
        for ffmpeg_path in ffmpeg_paths:
            try:
                subprocess.run([ffmpeg_path, '-version'], capture_output=True, check=True)
                self.ffmpeg_path = ffmpeg_path
                self.status_label.config(text="FFmpeg is ready", foreground='green')
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        self.status_label.config(text="FFmpeg not found! Please install FFmpeg", foreground='red')
        messagebox.showerror("Error", "FFmpeg is not installed or not in PATH. Please install FFmpeg first.")
    
    def browse_input_file(self):
        """Browse for input file"""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv"),
            ("Audio files", "*.mp3 *.wav *.aac *.flac *.ogg"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.input_file.set(filename)
            # Auto-generate output filename
            base_name = os.path.splitext(filename)[0]
            self.output_file.set(f"{base_name}_processed.mp4")
    
    def browse_output_file(self):
        """Browse for output file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
    
    def browse_subtitle_file(self):
        """Browse for subtitle file"""
        filetypes = [
            ("Subtitle files", "*.srt *.ass *.ssa *.vtt *.sub *.idx"),
            ("SRT files", "*.srt"),
            ("ASS/SSA files", "*.ass *.ssa"),
            ("WebVTT files", "*.vtt"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.subtitle_file.set(filename)
    
    def browse_bg_music(self):
        """Browse for background music file"""
        filetypes = [
            ("Audio files", "*.mp3 *.wav *.aac *.flac *.ogg *.m4a"),
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("AAC files", "*.aac"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.bg_music_file.set(filename)
    
    def browse_sound_effect(self):
        """Browse for sound effect file"""
        filetypes = [
            ("Audio files", "*.mp3 *.wav *.aac *.flac *.ogg *.m4a"),
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("AAC files", "*.aac"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.sound_effect_file.set(filename)
    
    def update_status(self, message, color='blue'):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
        self.root.update()
    
    def run_ffmpeg_command(self, command, description):
        """Run FFmpeg command in a separate thread"""
        def run_command():
            try:
                self.progress.start()
                self.update_status(f"Processing: {description}", 'blue')
                
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                
                self.progress.stop()
                self.update_status(f"Success: {description}", 'green')
                messagebox.showinfo("Success", f"{description} completed successfully!")
                
            except subprocess.CalledProcessError as e:
                self.progress.stop()
                self.update_status(f"Error: {description}", 'red')
                messagebox.showerror("Error", f"FFmpeg error: {e.stderr}")
            except Exception as e:
                self.progress.stop()
                self.update_status(f"Error: {description}", 'red')
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
        
        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()
    
    def convert_video(self):
        """Convert video format"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not output_path:
            messagebox.showerror("Error", "Please specify an output file")
            return
        
        # Get video codec from advanced options
        video_codec = "libx264"  # Default
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-c:v', video_codec,
            '-c:a', 'aac',
            '-crf', self.quality.get(),
            '-preset', 'medium',
            '-y',  # Overwrite output file
            output_path
        ]
        
        self.run_ffmpeg_command(command, "Video Conversion")
    
    def trim_video(self):
        """Trim video to specified duration"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not output_path:
            messagebox.showerror("Error", "Please specify an output file")
            return
        
        if self.ultra_precise.get():
            # Ultra precise trimming with 2-pass approach
            self.run_ultra_precise_trim(input_path, output_path)
        elif self.precise_trim.get():
            # Precise trimming with re-encoding for frame-accurate cuts
            # Use input seeking for better accuracy
            command = [
                self.ffmpeg_path, 
                '-ss', self.start_time.get(),  # Seek before input for better accuracy
                '-i', input_path,
                '-t', self.duration.get(),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-crf', self.quality.get(),
                '-preset', 'fast',
                '-avoid_negative_ts', 'make_zero',
                '-vsync', 'cfr',  # Constant frame rate
                '-y',
                output_path
            ]
            self.run_ffmpeg_command(command, "Video Trimming")
        else:
            # Fast trimming with copy (may have keyframe limitations)
            command = [
                self.ffmpeg_path, '-i', input_path,
                '-ss', self.start_time.get(),
                '-t', self.duration.get(),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                '-y',
                output_path
            ]
        
        self.run_ffmpeg_command(command, "Video Trimming")
    
    def run_ultra_precise_trim(self, input_path, output_path):
        """Ultra precise trimming using 2-pass approach"""
        def run_ultra_trim():
            try:
                self.progress.start()
                self.update_status("Ultra Precise Trimming: Pass 1/2", 'blue')
                
                # First pass: Extract a slightly larger segment to ensure we have the right frames
                temp_file = "temp_trim.mp4"
                start_time = self.start_time.get()
                duration = self.duration.get()
                
                # Parse time to add a small buffer
                start_parts = start_time.split(':')
                start_seconds = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
                
                # Subtract 1 second for buffer, but not below 0
                buffer_start = max(0, start_seconds - 1)
                buffer_start_time = f"{buffer_start//3600:02d}:{(buffer_start%3600)//60:02d}:{buffer_start%60:02d}"
                
                # Add 2 seconds to duration for buffer
                duration_parts = duration.split(':')
                duration_seconds = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])
                buffer_duration_seconds = duration_seconds + 2
                buffer_duration = f"{buffer_duration_seconds//3600:02d}:{(buffer_duration_seconds%3600)//60:02d}:{buffer_duration_seconds%60:02d}"
                
                # First pass: Extract buffered segment
                command1 = [
                    self.ffmpeg_path, '-ss', buffer_start_time, '-i', input_path,
                    '-t', buffer_duration, '-c:v', 'libx264', '-c:a', 'aac',
                    '-crf', self.quality.get(), '-preset', 'fast', '-y', temp_file
                ]
                
                subprocess.run(command1, check=True, capture_output=True)
                
                self.update_status("Ultra Precise Trimming: Pass 2/2", 'blue')
                
                # Second pass: Trim precisely from the buffered segment
                # Calculate offset within the buffered segment
                offset_seconds = 1  # We added 1 second buffer at start
                offset_time = f"{offset_seconds//3600:02d}:{(offset_seconds%3600)//60:02d}:{offset_seconds%60:02d}"
                
                command2 = [
                    self.ffmpeg_path, '-ss', offset_time, '-i', temp_file,
                    '-t', duration, '-c:v', 'libx264', '-c:a', 'aac',
                    '-crf', self.quality.get(), '-preset', 'fast',
                    '-avoid_negative_ts', 'make_zero', '-y', output_path
                ]
                
                subprocess.run(command2, check=True, capture_output=True)
                
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
                self.progress.stop()
                self.update_status("Ultra Precise Trimming completed!", 'green')
                messagebox.showinfo("Success", "Ultra Precise Trimming completed successfully!")
                
            except subprocess.CalledProcessError as e:
                self.progress.stop()
                self.update_status("Error: Ultra Precise Trimming failed", 'red')
                messagebox.showerror("Error", f"Ultra Precise Trimming error: {e.stderr}")
            except Exception as e:
                self.progress.stop()
                self.update_status("Error: Ultra Precise Trimming failed", 'red')
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            finally:
                # Clean up temp file if it exists
                if os.path.exists("temp_trim.mp4"):
                    os.remove("temp_trim.mp4")
        
        thread = threading.Thread(target=run_ultra_trim)
        thread.daemon = True
        thread.start()
    
    def extract_audio(self):
        """Extract audio from video"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_audio.mp3"
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-vn',  # No video
            '-acodec', 'mp3',
            '-ab', '192k',
            '-y',
            output_path
        ]
        
        self.run_ffmpeg_command(command, "Audio Extraction")
    
    def create_gif(self):
        """Create GIF from video"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.gif"
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-ss', self.start_time.get(),
            '-t', self.duration.get(),
            '-vf', f'scale={self.scale_width.get()}:{self.scale_height.get()}:flags=lanczos,palettegen',
            '-y',
            'palette.png'
        ]
        
        # First generate palette
        try:
            subprocess.run(command, check=True, capture_output=True)
            
            # Then create GIF
            gif_command = [
                self.ffmpeg_path, '-i', input_path,
                '-i', 'palette.png',
                '-ss', self.start_time.get(),
                '-t', self.duration.get(),
                '-filter_complex', f'[0:v]scale={self.scale_width.get()}:{self.scale_height.get()}:flags=lanczos[v];[v][1:v]paletteuse',
                '-y',
                output_path
            ]
            
            self.run_ffmpeg_command(gif_command, "GIF Creation")
            
            # Clean up palette file
            if os.path.exists('palette.png'):
                os.remove('palette.png')
                
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error creating GIF: {e.stderr}")
    
    def get_media_info(self):
        """Get media file information"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        
        # Use ffprobe from the same location as ffmpeg
        ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
        command = [
            ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
            input_path
        ]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            import json
            info = json.loads(result.stdout)
            
            # Create info window
            info_window = tk.Toplevel(self.root)
            info_window.title("Media Information")
            info_window.geometry("600x400")
            
            text_widget = tk.Text(info_window, wrap=tk.WORD, padx=10, pady=10)
            scrollbar = ttk.Scrollbar(info_window, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            # Format information
            text_widget.insert(tk.END, "=== FORMAT INFORMATION ===\n")
            format_info = info.get('format', {})
            for key, value in format_info.items():
                if key not in ['tags']:
                    text_widget.insert(tk.END, f"{key}: {value}\n")
            
            text_widget.insert(tk.END, "\n=== STREAM INFORMATION ===\n")
            for i, stream in enumerate(info.get('streams', [])):
                text_widget.insert(tk.END, f"\nStream {i}:\n")
                for key, value in stream.items():
                    if key not in ['tags', 'side_data_list']:
                        text_widget.insert(tk.END, f"  {key}: {value}\n")
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error getting media info: {e.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def add_subtitles(self):
        """Add subtitles to video (soft subtitles)"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not self.subtitle_file.get():
            messagebox.showerror("Error", "Please select a subtitle file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        subtitle_path = self.subtitle_file.get()
        
        if not output_path:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_with_subs.mp4"
            self.output_file.set(output_path)
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-i', subtitle_path,
            '-c:v', 'copy',  # Copy video without re-encoding
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-c:s', 'mov_text',  # Use mov_text for MP4 subtitles
            '-map', '0:v',  # Map video from first input
            '-map', '0:a',  # Map audio from first input
            '-map', '1:s',  # Map subtitles from second input
            '-y', output_path
        ]
        
        self.run_ffmpeg_command(command, "Adding Subtitles")
    
    def burn_subtitles_to_video(self):
        """Burn subtitles into video (hardcoded)"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not self.subtitle_file.get():
            messagebox.showerror("Error", "Please select a subtitle file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        subtitle_path = self.subtitle_file.get()
        
        if not output_path:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_burned_subs.mp4"
            self.output_file.set(output_path)
        
        # Create subtitle filter - use safe approach for Windows
        import shutil
        safe_srt = "safe_burn_subtitles.srt"
        shutil.copy2(subtitle_path, safe_srt)
        
        subtitle_filter = f"subtitles={safe_srt}"
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-crf', self.quality.get(),
            '-preset', 'medium',
            '-y', output_path
        ]
        
        # Run command with cleanup
        def run_burn_with_cleanup():
            try:
                subprocess.run(command, check=True, capture_output=True)
                messagebox.showinfo("Success", "Subtitles burned successfully!")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to burn subtitles: {e.stderr}")
            finally:
                # Clean up safe subtitle file
                if os.path.exists(safe_srt):
                    os.remove(safe_srt)
        
        import threading
        thread = threading.Thread(target=run_burn_with_cleanup)
        thread.daemon = True
        thread.start()
    
    def extract_subtitles_from_video(self):
        """Extract subtitles from video"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_extracted.srt"
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-map', '0:s:0',  # Map first subtitle stream
            '-c:s', 'srt',  # Convert to SRT format
            '-y', output_path
        ]
        
        self.run_ffmpeg_command(command, "Extracting Subtitles")
    
    def convert_subtitles(self):
        """Convert subtitle format"""
        if not self.subtitle_file.get():
            messagebox.showerror("Error", "Please select a subtitle file")
            return
        
        subtitle_path = self.subtitle_file.get()
        base_name = os.path.splitext(subtitle_path)[0]
        
        # Ask user for output format
        format_dialog = tk.Toplevel(self.root)
        format_dialog.title("Select Output Format")
        format_dialog.geometry("300x150")
        format_dialog.transient(self.root)
        format_dialog.grab_set()
        
        ttk.Label(format_dialog, text="Select output subtitle format:").pack(pady=10)
        
        format_var = tk.StringVar(value="srt")
        format_frame = ttk.Frame(format_dialog)
        format_frame.pack(pady=10)
        
        formats = [("SRT", "srt"), ("ASS", "ass"), ("WebVTT", "vtt"), ("SUB", "sub")]
        for text, value in formats:
            ttk.Radiobutton(format_frame, text=text, variable=format_var, value=value).pack(anchor=tk.W)
        
        def do_convert():
            output_format = format_var.get()
            output_path = f"{base_name}_converted.{output_format}"
            format_dialog.destroy()
            
            command = [
                self.ffmpeg_path, '-i', subtitle_path,
                '-c:s', output_format,
                '-y', output_path
            ]
            
            self.run_ffmpeg_command(command, f"Converting to {output_format.upper()}")
        
        ttk.Button(format_dialog, text="Convert", command=do_convert).pack(pady=10)
    
    def create_subtitle_preview(self):
        """Create a preview of subtitles overlaid on video"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not self.subtitle_file.get():
            messagebox.showerror("Error", "Please select a subtitle file")
            return
        
        input_path = self.input_file.get()
        subtitle_path = self.subtitle_file.get()
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_subtitle_preview.mp4"
        
        # Create a short preview (first 30 seconds)
        subtitle_path_normalized = subtitle_path.replace('\\', '/')
        subtitle_filter = f"subtitles={subtitle_path_normalized}"
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-t', '00:00:30',  # 30 second preview
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-crf', '23',
            '-preset', 'fast',
            '-y', output_path
        ]
        
        self.run_ffmpeg_command(command, "Creating Subtitle Preview")
    
    def transcribe_audio(self):
        """Transcribe audio from video and generate subtitles automatically"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        
        # Ask user for transcription settings
        settings_dialog = tk.Toplevel(self.root)
        settings_dialog.title("Transcription Settings")
        settings_dialog.geometry("400x300")
        settings_dialog.transient(self.root)
        settings_dialog.grab_set()
        
        # Center the dialog
        settings_dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        ttk.Label(settings_dialog, text="Audio Transcription Settings", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Language selection
        lang_frame = ttk.Frame(settings_dialog)
        lang_frame.pack(pady=10)
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT, padx=5)
        lang_var = tk.StringVar(value="en-US")
        lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, width=15)
        lang_combo['values'] = ("en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ru-RU", "ja-JP", "ko-KR", "zh-CN")
        lang_combo.pack(side=tk.LEFT, padx=5)
        
        # Chunk duration
        chunk_frame = ttk.Frame(settings_dialog)
        chunk_frame.pack(pady=10)
        ttk.Label(chunk_frame, text="Chunk Duration (seconds):").pack(side=tk.LEFT, padx=5)
        chunk_var = tk.StringVar(value="30")
        ttk.Entry(chunk_frame, textvariable=chunk_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Note about natural speech chunks
        note_frame = ttk.Frame(settings_dialog)
        note_frame.pack(pady=10)
        ttk.Label(note_frame, text="Subtitles will appear in natural speech chunks", 
                 font=("Arial", 9, "italic")).pack()
        ttk.Label(note_frame, text="(based on punctuation and pauses)", 
                 font=("Arial", 8, "italic")).pack()
        
        # Buttons
        button_frame = ttk.Frame(settings_dialog)
        button_frame.pack(pady=20)
        
        def start_transcription():
            try:
                language = lang_var.get()
                chunk_duration = int(chunk_var.get())
                settings_dialog.destroy()
                
                # Start transcription in a separate thread
                threading.Thread(target=self._perform_transcription, 
                               args=(input_path, language, chunk_duration), 
                               daemon=True).start()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for chunk duration")
        
        ttk.Button(button_frame, text="Start Transcription", command=start_transcription).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=settings_dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def _perform_transcription(self, input_path, language, chunk_duration):
        """Perform the actual transcription"""
        try:
            # Show progress dialog
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Transcribing Audio")
            progress_dialog.geometry("400x150")
            progress_dialog.transient(self.root)
            progress_dialog.grab_set()
            
            # Center the dialog
            progress_dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
            
            ttk.Label(progress_dialog, text="Transcribing audio... This may take a while.", font=("Arial", 10)).pack(pady=20)
            progress_var = tk.StringVar(value="Extracting audio...")
            progress_label = ttk.Label(progress_dialog, textvariable=progress_var)
            progress_label.pack(pady=10)
            
            # Update progress
            def update_progress(message):
                progress_var.set(message)
                progress_dialog.update()
            
            # Extract audio from video
            update_progress("Extracting audio from video...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Extract audio using FFmpeg
            extract_command = [
                self.ffmpeg_path, '-i', input_path,
                '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                '-y', temp_audio_path
            ]
            
            subprocess.run(extract_command, check=True, capture_output=True)
            
            # Load audio file
            update_progress("Loading audio file...")
            audio = AudioSegment.from_wav(temp_audio_path)
            
            # Initialize speech recognition
            recognizer = sr.Recognizer()
            
            # Split audio into chunks
            update_progress("Splitting audio into chunks...")
            chunk_length = chunk_duration * 1000  # Convert to milliseconds
            chunks = [audio[i:i + chunk_length] for i in range(0, len(audio), chunk_length)]
            
            # Transcribe each chunk
            subtitles = []
            for i, chunk in enumerate(chunks):
                update_progress(f"Transcribing chunk {i+1}/{len(chunks)}...")
                
                # Export chunk to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as chunk_file:
                    chunk.export(chunk_file.name, format="wav")
                    chunk_path = chunk_file.name
                
                try:
                    # Transcribe chunk
                    with sr.AudioFile(chunk_path) as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data, language=language)
                        
                        if text.strip():
                            # Calculate timing for this chunk
                            chunk_start_time = i * chunk_duration
                            chunk_end_time = min(chunk_start_time + chunk_duration, (i + 1) * chunk_duration)
                            
                            # Split text into natural speech chunks based on punctuation and pauses
                            sentences = self._split_into_speech_chunks(text)
                            
                            # Calculate timing for each sentence within the chunk
                            total_chars = len(text)
                            if total_chars > 0:
                                for j, sentence in enumerate(sentences):
                                    if sentence.strip():
                                        # Calculate relative position within the chunk
                                        char_start = text.find(sentence)
                                        char_end = char_start + len(sentence)
                                        
                                        # Calculate timing based on character position
                                        relative_start = char_start / total_chars
                                        relative_end = char_end / total_chars
                                        
                                        subtitle_start = chunk_start_time + relative_start * (chunk_end_time - chunk_start_time)
                                        subtitle_end = chunk_start_time + relative_end * (chunk_end_time - chunk_start_time)
                                        
                                        # Ensure minimum duration and maximum duration
                                        min_duration = 1.0  # Minimum 1 second
                                        max_duration = 8.0  # Maximum 8 seconds
                                        
                                        actual_duration = subtitle_end - subtitle_start
                                        if actual_duration < min_duration:
                                            subtitle_end = subtitle_start + min_duration
                                        elif actual_duration > max_duration:
                                            subtitle_end = subtitle_start + max_duration
                                        
                                        # Ensure we don't exceed chunk boundaries
                                        subtitle_end = min(subtitle_end, chunk_end_time)
                                        
                                        subtitles.append({
                                            'start': subtitle_start,
                                            'end': subtitle_end,
                                            'text': sentence.strip()
                                        })
                
                except sr.UnknownValueError:
                    # Could not understand audio
                    pass
                except sr.RequestError as e:
                    messagebox.showerror("Error", f"Speech recognition service error: {e}")
                    return
                finally:
                    # Clean up chunk file
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
            
            # Generate SRT file
            update_progress("Generating subtitle file...")
            base_name = os.path.splitext(input_path)[0]
            srt_path = f"{base_name}_transcribed.srt"
            
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                for i, subtitle in enumerate(subtitles, 1):
                    start_time_str = self._format_srt_time(subtitle['start'])
                    end_time_str = self._format_srt_time(subtitle['end'])
                    srt_file.write(f"{i}\n")
                    srt_file.write(f"{start_time_str} --> {end_time_str}\n")
                    srt_file.write(f"{subtitle['text']}\n\n")
            
            # Burn subtitles directly into video
            update_progress("Burning subtitles into video...")
            output_path = f"{base_name}_with_subtitles{os.path.splitext(input_path)[1]}"
            
            # Use safe approach for Windows subtitle filter
            import shutil
            safe_srt = "safe_transcribed_subtitles.srt"
            shutil.copy2(srt_path, safe_srt)
            
            subtitle_filter = f"subtitles={safe_srt}"
            
            burn_command = [
                self.ffmpeg_path, '-i', input_path,
                '-vf', subtitle_filter,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-crf', '23',
                '-preset', 'medium',
                '-y', output_path
            ]
            
            def run_burn_with_cleanup():
                try:
                    subprocess.run(burn_command, check=True, capture_output=True)
                    progress_dialog.destroy()
                    messagebox.showinfo("Success", f"Transcription and subtitle burning completed!\nVideo saved as: {output_path}")
                except subprocess.CalledProcessError as e:
                    progress_dialog.destroy()
                    messagebox.showerror("Error", f"Failed to burn subtitles: {e.stderr}")
                finally:
                    # Clean up files
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                    if os.path.exists(safe_srt):
                        os.remove(safe_srt)
                    if os.path.exists(srt_path):
                        os.remove(srt_path)  # Remove the temporary SRT file
            
            # Run burning in a separate thread
            threading.Thread(target=run_burn_with_cleanup, daemon=True).start()
            
        except Exception as e:
            if 'progress_dialog' in locals():
                progress_dialog.destroy()
            messagebox.showerror("Error", f"Transcription failed: {str(e)}")
    
    def _format_srt_time(self, seconds):
        """Format seconds into SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _split_into_speech_chunks(self, text):
        """Split text into natural speech chunks based on punctuation and pauses"""
        import re
        
        # First, split by major punctuation (periods, exclamation, question marks)
        # but keep the punctuation with the sentence
        sentences = re.split(r'([.!?]+)', text)
        
        # Recombine sentences with their punctuation
        combined_sentences = []
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
            else:
                sentence = sentences[i]
            
            if sentence.strip():
                combined_sentences.append(sentence.strip())
        
        # If no major punctuation found, split by commas and semicolons
        if len(combined_sentences) == 1 and len(combined_sentences[0]) > 50:
            # Split by commas and semicolons
            comma_splits = re.split(r'([,;]+)', combined_sentences[0])
            comma_combined = []
            for i in range(0, len(comma_splits), 2):
                if i + 1 < len(comma_splits):
                    part = comma_splits[i] + comma_splits[i + 1]
                else:
                    part = comma_splits[i]
                
                if part.strip():
                    comma_combined.append(part.strip())
            
            # If still too long, split by conjunctions
            if len(comma_combined) == 1 and len(comma_combined[0]) > 40:
                conjunction_splits = re.split(r'\s+(and|but|or|so|yet|for|nor)\s+', comma_combined[0], flags=re.IGNORECASE)
                final_sentences = []
                for i in range(0, len(conjunction_splits), 2):
                    if i + 1 < len(conjunction_splits):
                        part = conjunction_splits[i] + " " + conjunction_splits[i + 1]
                    else:
                        part = conjunction_splits[i]
                    
                    if part.strip():
                        final_sentences.append(part.strip())
                
                return final_sentences if final_sentences else [combined_sentences[0]]
            else:
                return comma_combined if comma_combined else [combined_sentences[0]]
        
        return combined_sentences if combined_sentences else [text]
    
    def add_background_music(self):
        """Add background music to video"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not self.bg_music_file.get():
            messagebox.showerror("Error", "Please select a background music file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        music_path = self.bg_music_file.get()
        
        if not output_path:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_with_music.mp4"
            self.output_file.set(output_path)
        
        # Create audio filter for mixing
        bg_volume = self.bg_volume.get()
        if self.mix_audio.get():
            # Mix background music with original audio
            audio_filter = f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=3[out]"
            command = [
                self.ffmpeg_path, '-i', input_path, '-i', music_path,
                '-filter_complex', audio_filter,
                '-map', '0:v', '-map', '[out]',
                '-c:v', 'copy', '-c:a', 'aac',
                '-y', output_path
            ]
        else:
            # Replace original audio with background music
            command = [
                self.ffmpeg_path, '-i', input_path, '-i', music_path,
                '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac',
                '-shortest',  # Match video duration
                '-y', output_path
            ]
        
        self.run_ffmpeg_command(command, "Adding Background Music")
    
    def add_sound_effect(self):
        """Add sound effect to video with timing controls"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not self.sound_effect_file.get():
            messagebox.showerror("Error", "Please select a sound effect file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        effect_path = self.sound_effect_file.get()
        
        if not output_path:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_with_effect.mp4"
            self.output_file.set(output_path)
        
        # Get timing parameters
        try:
            start_time = float(self.effect_start_time.get()) if self.effect_start_time.get() else 0.0
            duration = float(self.effect_duration.get()) if self.effect_duration.get() else None
            effect_volume = float(self.effect_volume.get())
            loop_effect = self.loop_effect.get()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for timing")
            return
        
        # Build FFmpeg command with proper timing for sound effect
        command = [self.ffmpeg_path, '-i', input_path, '-i', effect_path]
        
        # Create audio filter with timing
        if self.replace_audio.get():
            # Replace original audio with timed effect
            if start_time > 0 or duration:
                # Create silence for the delay, then add the effect
                filter_steps = []
                
                # First, create silence for the delay period
                if start_time > 0:
                    filter_steps.append(f"anullsrc=channel_layout=stereo:sample_rate=44100[silence]")
                    filter_steps.append(f"[silence]atrim=duration={start_time}[silence_trimmed]")
                
                # Process the sound effect
                effect_input = "[1:a]"
                if duration:
                    effect_input = f"[1:a]atrim=duration={duration}[effect_trimmed]"
                    filter_steps.append(effect_input)
                    effect_input = "[effect_trimmed]"
                
                filter_steps.append(f"{effect_input}volume={effect_volume}[effect_vol]")
                
                # Concatenate silence + effect
                if start_time > 0:
                    filter_steps.append(f"[silence_trimmed][effect_vol]concat=n=2:v=0:a=1[effect]")
                else:
                    filter_steps.append(f"[effect_vol]asplit[effect]")
                
                audio_filter = ";".join(filter_steps)
            else:
                audio_filter = f"[1:a]volume={effect_volume}[effect]"
            command.extend(['-filter_complex', audio_filter, '-map', '0:v', '-map', '[effect]'])
        else:
            # Mix with original audio using proper timing
            if start_time > 0 or duration:
                # Create silence for delay, then add effect
                filter_steps = []
                
                # Create silence for the delay period
                if start_time > 0:
                    filter_steps.append(f"anullsrc=channel_layout=stereo:sample_rate=44100[silence]")
                    filter_steps.append(f"[silence]atrim=duration={start_time}[silence_trimmed]")
                
                # Process the sound effect
                effect_input = "[1:a]"
                if duration:
                    effect_input = f"[1:a]atrim=duration={duration}[effect_trimmed]"
                    filter_steps.append(effect_input)
                    effect_input = "[effect_trimmed]"
                
                filter_steps.append(f"{effect_input}volume={effect_volume}[effect_vol]")
                
                # Concatenate silence + effect
                if start_time > 0:
                    filter_steps.append(f"[silence_trimmed][effect_vol]concat=n=2:v=0:a=1[effect]")
                else:
                    filter_steps.append(f"[effect_vol]asplit[effect]")
                
                # Mix with original audio
                filter_steps.append(f"[0:a][effect]amix=inputs=2:duration=first:dropout_transition=3[out]")
                audio_filter = ";".join(filter_steps)
            else:
                # Simple mix without timing
                audio_filter = f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=3:weights=1 {effect_volume}[out]"
            
            command.extend(['-filter_complex', audio_filter, '-map', '0:v', '-map', '[out]'])
        
        command.extend(['-c:v', 'copy', '-c:a', 'aac', '-y', output_path])
        
        self.run_ffmpeg_command(command, "Adding Sound Effect")
    
    def open_audio_mixer(self):
        """Open advanced audio mixer window"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file first")
            return
        
        AudioMixer(self.root, self.input_file.get(), self.ffmpeg_path)
    
    def add_fade_effects(self):
        """Add fade in/out effects to audio"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not output_path:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_faded.mp4"
            self.output_file.set(output_path)
        
        # Create fade dialog
        fade_dialog = tk.Toplevel(self.root)
        fade_dialog.title("Fade Effects")
        fade_dialog.geometry("400x300")
        fade_dialog.transient(self.root)
        fade_dialog.grab_set()
        
        ttk.Label(fade_dialog, text="Audio Fade Effects", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Fade in
        fade_in_frame = ttk.Frame(fade_dialog)
        fade_in_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.fade_in_enabled = tk.BooleanVar()
        ttk.Checkbutton(fade_in_frame, text="Fade In", variable=self.fade_in_enabled).pack(side=tk.LEFT)
        
        ttk.Label(fade_in_frame, text="Duration (seconds):").pack(side=tk.LEFT, padx=(20, 5))
        self.fade_in_duration = tk.StringVar(value="2")
        ttk.Entry(fade_in_frame, textvariable=self.fade_in_duration, width=8).pack(side=tk.LEFT)
        
        # Fade out
        fade_out_frame = ttk.Frame(fade_dialog)
        fade_out_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.fade_out_enabled = tk.BooleanVar()
        ttk.Checkbutton(fade_out_frame, text="Fade Out", variable=self.fade_out_enabled).pack(side=tk.LEFT)
        
        ttk.Label(fade_out_frame, text="Duration (seconds):").pack(side=tk.LEFT, padx=(20, 5))
        self.fade_out_duration = tk.StringVar(value="2")
        ttk.Entry(fade_out_frame, textvariable=self.fade_out_duration, width=8).pack(side=tk.LEFT)
        
        def apply_fade():
            fade_in_dur = self.fade_in_duration.get()
            fade_out_dur = self.fade_out_duration.get()
            
            # Build audio filter
            audio_filters = []
            if self.fade_in_enabled.get():
                audio_filters.append(f"afade=t=in:ss=0:d={fade_in_dur}")
            if self.fade_out_enabled.get():
                audio_filters.append(f"afade=t=out:st=0:d={fade_out_dur}")
            
            if not audio_filters:
                messagebox.showwarning("Warning", "Please select at least one fade effect")
                return
            
            audio_filter = ",".join(audio_filters)
            
            command = [
                self.ffmpeg_path, '-i', input_path,
                '-af', audio_filter,
                '-c:v', 'copy', '-c:a', 'aac',
                '-y', output_path
            ]
            
            fade_dialog.destroy()
            self.run_ffmpeg_command(command, "Adding Fade Effects")
        
        ttk.Button(fade_dialog, text="Apply Fade Effects", command=apply_fade).pack(pady=20)
    
    def normalize_audio(self):
        """Normalize audio levels"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not output_path:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_normalized.mp4"
            self.output_file.set(output_path)
        
        # Normalize audio using loudnorm filter
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-af', 'loudnorm',
            '-c:v', 'copy', '-c:a', 'aac',
            '-y', output_path
        ]
        
        self.run_ffmpeg_command(command, "Normalizing Audio")
    
    def apply_video_effects(self):
        """Apply video effects and filters"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not output_path:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_with_effects.mp4"
            self.output_file.set(output_path)
        
        # Build video filter chain
        filters = []
        
        # Basic effects
        blur = float(self.blur_strength.get())
        if blur > 0:
            filters.append(f"gblur=sigma={blur}")
        
        brightness = float(self.brightness.get())
        contrast = float(self.contrast.get())
        saturation = float(self.saturation.get())
        
        # Artistic filters
        artistic_filter = self.artistic_filter.get()
        
        # Combine basic effects and artistic filters into single eq filter if needed
        if artistic_filter == "vintage":
            # For vintage, use the artistic filter's eq settings
            if brightness != 0 or contrast != 1 or saturation != 1:
                # Combine user settings with vintage settings
                final_brightness = brightness + 0.1
                final_contrast = contrast * 1.1
                final_saturation = saturation * 0.8
                filters.append(f"eq=brightness={final_brightness}:contrast={final_contrast}:saturation={final_saturation}")
            else:
                filters.append("eq=contrast=1.1:brightness=0.1:saturation=0.8")
            filters.append("colorbalance=rs=0.3:gs=-0.1:bs=-0.2")
        else:
            # For other filters, apply basic effects normally
            if brightness != 0 or contrast != 1 or saturation != 1:
                filters.append(f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}")
            
            if artistic_filter != "none":
                if artistic_filter == "black & white":
                    filters.append("hue=s=0")
                elif artistic_filter == "sepia":
                    filters.append("colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131")
                elif artistic_filter == "negative":
                    filters.append("negate")
                elif artistic_filter == "emboss":
                    filters.append("convolution=0 -1 0 -1 5 -1 0 -1 0:0 -1 0 -1 5 -1 0 -1 0:0 -1 0 -1 5 -1 0 -1 0:0 -1 0 -1 5 -1 0 -1 0")
                elif artistic_filter == "edge detection":
                    filters.append("edgedetect=low=0.1:high=0.4")
        
        # Motion effects
        if self.zoom_effect.get():
            filters.append("zoompan=z='min(zoom+0.0015,1.5)':d=25:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720")
        
        rotation = float(self.rotation.get())
        if rotation != 0:
            filters.append(f"rotate={rotation * 3.14159 / 180}")
        
        if self.horizontal_flip.get():
            filters.append("hflip")
        
        if self.vertical_flip.get():
            filters.append("vflip")
        
        # Build command
        command = [self.ffmpeg_path, '-i', input_path]
        
        if filters:
            # Join filters with commas to build a single linear filter chain
            command.extend(['-vf', ','.join(filters)])
        
        command.extend(['-c:a', 'copy', '-y', output_path])
        
        self.run_ffmpeg_command(command, "Applying Video Effects")
    
    def preview_effects(self):
        """Create a preview of effects (first 30 seconds)"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file")
            return
        
        input_path = self.input_file.get()
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_effects_preview.mp4"
        
        # Build video filter chain (same as apply_video_effects)
        filters = []
        
        # Basic effects
        blur = float(self.blur_strength.get())
        if blur > 0:
            filters.append(f"gblur=sigma={blur}")
        
        brightness = float(self.brightness.get())
        contrast = float(self.contrast.get())
        saturation = float(self.saturation.get())
        
        if brightness != 0 or contrast != 1 or saturation != 1:
            filters.append(f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}")
        
        # Artistic filters
        artistic_filter = self.artistic_filter.get()
        if artistic_filter != "none":
            if artistic_filter == "black & white":
                filters.append("hue=s=0")
            elif artistic_filter == "sepia":
                filters.append("colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131")
            elif artistic_filter == "vintage":
                # Create vintage effect with color grading
                filters.append("eq=contrast=1.1:brightness=0.1:saturation=0.8")
                filters.append("colorbalance=rs=0.3:gs=-0.1:bs=-0.2")
            elif artistic_filter == "negative":
                filters.append("negate")
            elif artistic_filter == "emboss":
                filters.append("convolution=0 -1 0 -1 5 -1 0 -1 0:0 -1 0 -1 5 -1 0 -1 0:0 -1 0 -1 5 -1 0 -1 0:0 -1 0 -1 5 -1 0 -1 0")
            elif artistic_filter == "edge detection":
                filters.append("edgedetect=low=0.1:high=0.4")
        
        # Motion effects
        if self.zoom_effect.get():
            filters.append("zoompan=z='min(zoom+0.0015,1.5)':d=25:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720")
        
        rotation = float(self.rotation.get())
        if rotation != 0:
            filters.append(f"rotate={rotation * 3.14159 / 180}")
        
        if self.horizontal_flip.get():
            filters.append("hflip")
        
        if self.vertical_flip.get():
            filters.append("vflip")
        
        # Build command for preview
        command = [self.ffmpeg_path, '-i', input_path, '-t', '00:00:30']  # 30 second preview
        
        if filters:
            # Join filters with commas for a single chain in preview too
            command.extend(['-vf', ','.join(filters)])
        
        command.extend(['-c:v', 'libx264', '-c:a', 'aac', '-crf', '23', '-preset', 'fast', '-y', output_path])
        
        self.run_ffmpeg_command(command, "Creating Effects Preview")
    
    def reset_effects(self):
        """Reset all effects to default values"""
        self.blur_strength.set("0")
        self.brightness.set("0")
        self.contrast.set("1")
        self.saturation.set("1")
        self.artistic_filter.set("none")
        self.zoom_effect.set(False)
        self.rotation.set("0")
        self.horizontal_flip.set(False)
        self.vertical_flip.set(False)
        messagebox.showinfo("Reset", "All effects have been reset to default values")
    
    def open_subtitle_editor(self):
        """Open the subtitle editor window"""
        # Use input file if available, otherwise use a default
        video_path = self.input_file.get() if self.input_file.get() else "sample_video.mp4"
        
        try:
            print("Opening subtitle editor...")
            SubtitleEditor(self.root, video_path, self.ffmpeg_path)
            print("Subtitle editor opened successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open subtitle editor: {str(e)}")
            print(f"Error opening subtitle editor: {e}")

class AudioMixer:
    def __init__(self, parent, video_path, ffmpeg_path):
        self.parent = parent
        self.video_path = video_path
        self.ffmpeg_path = ffmpeg_path
        self.audio_tracks = []
        
        # Create mixer window
        self.mixer_window = tk.Toplevel(parent)
        self.mixer_window.title("Audio Mixer")
        self.mixer_window.geometry("800x600")
        self.mixer_window.transient(parent)
        self.mixer_window.grab_set()
        
        self.setup_mixer_ui()
    
    def setup_mixer_ui(self):
        """Setup the audio mixer interface with scrolling"""
        # Create scrollable container
        container = ttk.Frame(self.mixer_window)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main frame inside scrollable area
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video info
        info_frame = ttk.LabelFrame(main_frame, text="Video Information", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Video: {os.path.basename(self.video_path)}").pack(anchor=tk.W)
        
        # Add audio track section
        add_frame = ttk.LabelFrame(main_frame, text="Add Audio Track", padding="5")
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Audio file selection
        ttk.Label(add_frame, text="Audio File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.audio_file = tk.StringVar()
        file_frame = ttk.Frame(add_frame)
        file_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        file_frame.columnconfigure(0, weight=1)
        ttk.Entry(file_frame, textvariable=self.audio_file, width=40).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(file_frame, text="Browse", command=self.browse_audio_file).grid(row=0, column=1, padx=5)
        
        # Audio options
        options_frame = ttk.Frame(add_frame)
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(options_frame, text="Start Time:").pack(side=tk.LEFT, padx=(0, 5))
        self.start_time = tk.StringVar(value="00:00:00")
        ttk.Entry(options_frame, textvariable=self.start_time, width=12).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(options_frame, text="Volume:").pack(side=tk.LEFT, padx=(0, 5))
        self.volume = tk.StringVar(value="1.0")
        volume_scale = ttk.Scale(options_frame, from_=0, to=2, variable=self.volume, orient=tk.HORIZONTAL)
        volume_scale.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(options_frame, text="Loop:").pack(side=tk.LEFT, padx=(0, 5))
        self.loop_audio = tk.BooleanVar()
        ttk.Checkbutton(options_frame, variable=self.loop_audio).pack(side=tk.LEFT)
        
        ttk.Button(add_frame, text="Add Audio Track", command=self.add_audio_track).pack(pady=5)
        
        # Audio tracks list
        tracks_frame = ttk.LabelFrame(main_frame, text="Audio Tracks", padding="5")
        tracks_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for audio tracks
        columns = ('File', 'Start Time', 'Volume', 'Loop', 'Duration')
        self.tracks_tree = ttk.Treeview(tracks_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tracks_tree.heading(col, text=col)
            self.tracks_tree.column(col, width=120)
        
        self.tracks_tree.column('File', width=200)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(tracks_frame, orient=tk.VERTICAL, command=self.tracks_tree.yview)
        self.tracks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tracks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected_track).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all_tracks).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Preview Mix", command=self.preview_mix).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Apply Mix", command=self.apply_mix).pack(side=tk.LEFT, padx=5)
    
    def browse_audio_file(self):
        """Browse for audio file"""
        filetypes = [
            ("Audio files", "*.mp3 *.wav *.aac *.flac *.ogg *.m4a"),
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("AAC files", "*.aac"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.audio_file.set(filename)
    
    def add_audio_track(self):
        """Add audio track to mixer"""
        if not self.audio_file.get():
            messagebox.showerror("Error", "Please select an audio file")
            return
        
        audio_track = {
            'file': self.audio_file.get(),
            'start_time': self.start_time.get(),
            'volume': self.volume.get(),
            'loop': self.loop_audio.get()
        }
        
        self.audio_tracks.append(audio_track)
        self.refresh_tracks_list()
        
        # Clear entry
        self.audio_file.set("")
        self.start_time.set("00:00:00")
        self.volume.set("1.0")
        self.loop_audio.set(False)
    
    def refresh_tracks_list(self):
        """Refresh the audio tracks list"""
        # Clear existing items
        for item in self.tracks_tree.get_children():
            self.tracks_tree.delete(item)
        
        # Add tracks
        for i, track in enumerate(self.audio_tracks):
            filename = os.path.basename(track['file'])
            loop_text = "Yes" if track['loop'] else "No"
            
            self.tracks_tree.insert('', 'end', values=(
                filename,
                track['start_time'],
                track['volume'],
                loop_text,
                "Unknown"
            ))
    
    def remove_selected_track(self):
        """Remove selected audio track"""
        selection = self.tracks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a track to remove")
            return
        
        item = self.tracks_tree.item(selection[0])
        index = self.tracks_tree.index(selection[0])
        
        if 0 <= index < len(self.audio_tracks):
            self.audio_tracks.pop(index)
            self.refresh_tracks_list()
    
    def clear_all_tracks(self):
        """Clear all audio tracks"""
        if self.audio_tracks and messagebox.askyesno("Confirm", "Clear all audio tracks?"):
            self.audio_tracks.clear()
            self.refresh_tracks_list()
    
    def preview_mix(self):
        """Preview audio mix"""
        if not self.audio_tracks:
            messagebox.showwarning("Warning", "No audio tracks to mix")
            return
        
        # Create preview (first 30 seconds)
        base_name = os.path.splitext(self.video_path)[0]
        preview_path = f"{base_name}_audio_preview.mp4"
        
        command = self.build_mix_command(preview_path, preview=True)
        
        def run_preview():
            try:
                subprocess.run(command, check=True, capture_output=True)
                messagebox.showinfo("Success", f"Audio preview created: {preview_path}")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to create preview: {e.stderr}")
        
        import threading
        thread = threading.Thread(target=run_preview)
        thread.daemon = True
        thread.start()
    
    def apply_mix(self):
        """Apply audio mix to video"""
        if not self.audio_tracks:
            messagebox.showwarning("Warning", "No audio tracks to mix")
            return
        
        # Ask for output file
        base_name = os.path.splitext(self.video_path)[0]
        output_path = filedialog.asksaveasfilename(
            title="Save Video with Audio Mix",
            defaultextension=".mp4",
            initialfile=f"{base_name}_mixed_audio.mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        
        if output_path:
            command = self.build_mix_command(output_path)
            
            def run_apply():
                try:
                    subprocess.run(command, check=True, capture_output=True)
                    messagebox.showinfo("Success", f"Video with mixed audio saved: {output_path}")
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error", f"Failed to apply audio mix: {e.stderr}")
            
            import threading
            thread = threading.Thread(target=run_apply)
            thread.daemon = True
            thread.start()
    
    def build_mix_command(self, output_path, preview=False):
        """Build FFmpeg command for audio mixing"""
        # Start with video input
        command = [self.ffmpeg_path, '-i', self.video_path]
        
        # Add audio inputs
        for track in self.audio_tracks:
            command.extend(['-i', track['file']])
        
        # Build filter complex
        filter_parts = []
        
        # Get original audio
        filter_parts.append("[0:a]volume=1.0[orig]")
        
        # Process each audio track
        for i, track in enumerate(self.audio_tracks):
            input_idx = i + 1
            volume = track['volume']
            start_time = track['start_time']
            
            if track['loop']:
                filter_parts.append(f"[{input_idx}:a]volume={volume},aloop=loop=-1:size=2e+09[track{i}]")
            else:
                filter_parts.append(f"[{input_idx}:a]volume={volume}[track{i}]")
        
        # Mix all audio tracks
        mix_inputs = ["[orig]"] + [f"[track{i}]" for i in range(len(self.audio_tracks))]
        mix_filter = f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=3[out]"
        filter_parts.append(mix_filter)
        
        filter_complex = ";".join(filter_parts)
        
        # Build final command
        command.extend([
            '-filter_complex', filter_complex,
            '-map', '0:v',
            '-map', '[out]',
            '-c:v', 'copy',
            '-c:a', 'aac'
        ])
        
        if preview:
            command.extend(['-t', '00:00:30'])  # 30 second preview
        
        command.extend(['-y', output_path])
        
        return command

class SubtitleEditor:
    def __init__(self, parent, video_path, ffmpeg_path):
        self.parent = parent
        self.video_path = video_path
        self.ffmpeg_path = ffmpeg_path
        self.subtitles = []
        
        # Create editor window
        self.editor_window = tk.Toplevel(parent)
        self.editor_window.title("Subtitle Editor")
        self.editor_window.geometry("800x600")
        self.editor_window.transient(parent)
        self.editor_window.grab_set()
        
        self.setup_editor_ui()
        
    def setup_editor_ui(self):
        """Setup the subtitle editor interface with scrolling"""
        # Create scrollable container
        container = ttk.Frame(self.editor_window)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main frame inside scrollable area
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video info
        info_frame = ttk.LabelFrame(main_frame, text="Video Information", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Video: {os.path.basename(self.video_path)}").pack(anchor=tk.W)
        
        # Video duration
        self.video_duration = self.get_video_duration()
        if self.video_duration:
            duration_text = f"Duration: {self.format_time(self.video_duration)}"
            ttk.Label(info_frame, text=duration_text).pack(anchor=tk.W)
        
        # Subtitle entry frame
        entry_frame = ttk.LabelFrame(main_frame, text="Add Subtitle", padding="5")
        entry_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Time entry
        time_frame = ttk.Frame(entry_frame)
        time_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(time_frame, text="Start Time:").pack(side=tk.LEFT, padx=(0, 5))
        self.start_time_var = tk.StringVar(value="00:00:00")
        start_time_entry = ttk.Entry(time_frame, textvariable=self.start_time_var, width=12)
        start_time_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(time_frame, text="End Time:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_time_var = tk.StringVar(value="00:00:03")
        end_time_entry = ttk.Entry(time_frame, textvariable=self.end_time_var, width=12)
        end_time_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Quick time buttons
        ttk.Button(time_frame, text="Current", command=self.set_current_time).pack(side=tk.LEFT, padx=2)
        ttk.Button(time_frame, text="+1s", command=lambda: self.adjust_time(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(time_frame, text="+5s", command=lambda: self.adjust_time(5)).pack(side=tk.LEFT, padx=2)
        
        # Text entry
        text_frame = ttk.Frame(entry_frame)
        text_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(text_frame, text="Subtitle Text:").pack(anchor=tk.W)
        self.subtitle_text = tk.Text(text_frame, height=3, width=60)
        self.subtitle_text.pack(fill=tk.X, pady=2)
        
        # Add button
        ttk.Button(entry_frame, text="Add Subtitle", command=self.add_subtitle).pack(pady=5)
        
        # Subtitle list
        list_frame = ttk.LabelFrame(main_frame, text="Subtitles", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for subtitles
        columns = ('Index', 'Start', 'End', 'Duration', 'Text')
        self.subtitle_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.subtitle_tree.heading(col, text=col)
            self.subtitle_tree.column(col, width=100)
        
        self.subtitle_tree.column('Text', width=300)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.subtitle_tree.yview)
        self.subtitle_tree.configure(yscrollcommand=scrollbar.set)
        
        self.subtitle_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to edit
        self.subtitle_tree.bind('<Double-1>', self.edit_subtitle)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load SRT", command=self.load_srt).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save SRT", command=self.save_srt).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Preview", command=self.preview_subtitles).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Apply to Video", command=self.apply_subtitles).pack(side=tk.LEFT, padx=5)
        
    def get_video_duration(self):
        """Get video duration in seconds"""
        try:
            command = [
                self.ffmpeg_path, '-i', self.video_path,
                '-f', 'null', '-'
            ]
            result = subprocess.run(command, capture_output=True, text=True, stderr=subprocess.STDOUT)
            
            # Parse duration from FFmpeg output
            for line in result.stdout.split('\n'):
                if 'Duration:' in line:
                    duration_str = line.split('Duration:')[1].split(',')[0].strip()
                    return self.parse_time(duration_str)
            return None
        except:
            return None
    
    def parse_time(self, time_str):
        """Parse time string (HH:MM:SS.mmm) to seconds"""
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0
    
    def format_time(self, seconds):
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def set_current_time(self):
        """Set current time (placeholder - would need video player integration)"""
        # For now, just set to 00:00:00
        self.start_time_var.set("00:00:00")
        end_seconds = self.parse_time(self.start_time_var.get()) + 3
        self.end_time_var.set(self.format_time(end_seconds))
    
    def adjust_time(self, seconds):
        """Adjust current time by given seconds"""
        current = self.parse_time(self.start_time_var.get())
        new_time = max(0, current + seconds)
        self.start_time_var.set(self.format_time(new_time))
        
        # Also adjust end time
        end_current = self.parse_time(self.end_time_var.get())
        end_new = max(new_time + 1, end_current + seconds)
        self.end_time_var.set(self.format_time(end_new))
    
    def add_subtitle(self):
        """Add a new subtitle"""
        start_time = self.start_time_var.get()
        end_time = self.end_time_var.get()
        text = self.subtitle_text.get("1.0", tk.END).strip()
        
        if not text:
            messagebox.showerror("Error", "Please enter subtitle text")
            return
        
        if not self.validate_time_format(start_time) or not self.validate_time_format(end_time):
            messagebox.showerror("Error", "Invalid time format. Use HH:MM:SS")
            return
        
        if self.parse_time(start_time) >= self.parse_time(end_time):
            messagebox.showerror("Error", "Start time must be before end time")
            return
        
        # Add to list
        subtitle = {
            'start': start_time,
            'end': end_time,
            'text': text
        }
        self.subtitles.append(subtitle)
        
        # Update display
        self.refresh_subtitle_list()
        
        # Clear entry
        self.subtitle_text.delete("1.0", tk.END)
        # Set next start time to current end time
        self.start_time_var.set(end_time)
        next_end = self.parse_time(end_time) + 3
        self.end_time_var.set(self.format_time(next_end))
    
    def validate_time_format(self, time_str):
        """Validate time format HH:MM:SS"""
        try:
            parts = time_str.split(':')
            if len(parts) != 3:
                return False
            int(parts[0])  # hours
            int(parts[1])  # minutes
            int(parts[2])  # seconds
            return True
        except:
            return False
    
    def refresh_subtitle_list(self):
        """Refresh the subtitle list display"""
        # Clear existing items
        for item in self.subtitle_tree.get_children():
            self.subtitle_tree.delete(item)
        
        # Add subtitles
        for i, subtitle in enumerate(self.subtitles):
            start_seconds = self.parse_time(subtitle['start'])
            end_seconds = self.parse_time(subtitle['end'])
            duration = end_seconds - start_seconds
            
            self.subtitle_tree.insert('', 'end', values=(
                i + 1,
                subtitle['start'],
                subtitle['end'],
                f"{duration:.1f}s",
                subtitle['text'][:50] + "..." if len(subtitle['text']) > 50 else subtitle['text']
            ))
    
    def edit_selected(self):
        """Edit selected subtitle"""
        selection = self.subtitle_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a subtitle to edit")
            return
        
        item = self.subtitle_tree.item(selection[0])
        index = int(item['values'][0]) - 1
        
        if 0 <= index < len(self.subtitles):
            self.edit_subtitle_dialog(index)
    
    def edit_subtitle(self, event):
        """Edit subtitle on double-click"""
        self.edit_selected()
    
    def edit_subtitle_dialog(self, index):
        """Open edit dialog for subtitle"""
        subtitle = self.subtitles[index]
        
        edit_window = tk.Toplevel(self.editor_window)
        edit_window.title("Edit Subtitle")
        edit_window.geometry("400x200")
        edit_window.transient(self.editor_window)
        edit_window.grab_set()
        
        # Start time
        ttk.Label(edit_window, text="Start Time:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        start_var = tk.StringVar(value=subtitle['start'])
        ttk.Entry(edit_window, textvariable=start_var, width=12).grid(row=0, column=1, padx=5, pady=5)
        
        # End time
        ttk.Label(edit_window, text="End Time:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        end_var = tk.StringVar(value=subtitle['end'])
        ttk.Entry(edit_window, textvariable=end_var, width=12).grid(row=1, column=1, padx=5, pady=5)
        
        # Text
        ttk.Label(edit_window, text="Text:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        text_widget = tk.Text(edit_window, height=4, width=40)
        text_widget.grid(row=2, column=1, padx=5, pady=5)
        text_widget.insert("1.0", subtitle['text'])
        
        def save_changes():
            new_start = start_var.get()
            new_end = end_var.get()
            new_text = text_widget.get("1.0", tk.END).strip()
            
            if not new_text:
                messagebox.showerror("Error", "Subtitle text cannot be empty")
                return
            
            if not self.validate_time_format(new_start) or not self.validate_time_format(new_end):
                messagebox.showerror("Error", "Invalid time format. Use HH:MM:SS")
                return
            
            if self.parse_time(new_start) >= self.parse_time(new_end):
                messagebox.showerror("Error", "Start time must be before end time")
                return
            
            # Update subtitle
            self.subtitles[index] = {
                'start': new_start,
                'end': new_end,
                'text': new_text
            }
            
            self.refresh_subtitle_list()
            edit_window.destroy()
        
        ttk.Button(edit_window, text="Save", command=save_changes).grid(row=3, column=1, padx=5, pady=10)
    
    def delete_selected(self):
        """Delete selected subtitle"""
        selection = self.subtitle_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a subtitle to delete")
            return
        
        item = self.subtitle_tree.item(selection[0])
        index = int(item['values'][0]) - 1
        
        if 0 <= index < len(self.subtitles):
            self.subtitles.pop(index)
            self.refresh_subtitle_list()
    
    def clear_all(self):
        """Clear all subtitles"""
        if self.subtitles and messagebox.askyesno("Confirm", "Clear all subtitles?"):
            self.subtitles.clear()
            self.refresh_subtitle_list()
    
    def load_srt(self):
        """Load subtitles from SRT file"""
        filename = filedialog.askopenfilename(
            title="Load SRT File",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.subtitles = self.parse_srt_file(filename)
                self.refresh_subtitle_list()
                messagebox.showinfo("Success", f"Loaded {len(self.subtitles)} subtitles")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load SRT file: {str(e)}")
    
    def parse_srt_file(self, filename):
        """Parse SRT file and return subtitle list"""
        subtitles = []
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by double newlines to get subtitle blocks
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Skip index line, get time line
                time_line = lines[1]
                text_lines = lines[2:]
                
                # Parse time line (00:00:00,000 --> 00:00:03,000)
                if ' --> ' in time_line:
                    start_str, end_str = time_line.split(' --> ')
                    start_time = start_str.replace(',', '.').strip()
                    end_time = end_str.replace(',', '.').strip()
                    
                    # Convert to HH:MM:SS format
                    start_formatted = self.convert_srt_time(start_time)
                    end_formatted = self.convert_srt_time(end_time)
                    
                    subtitle = {
                        'start': start_formatted,
                        'end': end_formatted,
                        'text': '\n'.join(text_lines)
                    }
                    subtitles.append(subtitle)
        
        return subtitles
    
    def convert_srt_time(self, srt_time):
        """Convert SRT time format to HH:MM:SS"""
        try:
            # Remove milliseconds
            time_part = srt_time.split('.')[0]
            return time_part
        except:
            return "00:00:00"
    
    def save_srt(self):
        """Save subtitles to SRT file"""
        if not self.subtitles:
            messagebox.showwarning("Warning", "No subtitles to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save SRT File",
            defaultextension=".srt",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.write_srt_file(filename)
                messagebox.showinfo("Success", f"Saved {len(self.subtitles)} subtitles to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save SRT file: {str(e)}")
    
    def write_srt_file(self, filename):
        """Write subtitles to SRT file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(self.subtitles):
                f.write(f"{i + 1}\n")
                f.write(f"{subtitle['start']},000 --> {subtitle['end']},000\n")
                f.write(f"{subtitle['text']}\n\n")
    
    def preview_subtitles(self):
        """Preview subtitles on video"""
        if not self.subtitles:
            messagebox.showwarning("Warning", "No subtitles to preview")
            return
        
        # Save temporary SRT file
        temp_srt = "temp_preview.srt"
        self.write_srt_file(temp_srt)
        
        # Create preview video
        base_name = os.path.splitext(self.video_path)[0]
        preview_path = f"{base_name}_subtitle_preview.mp4"
        
        # Use safe subtitle file approach
        import shutil
        safe_srt = "safe_preview_subtitles.srt"
        shutil.copy2(temp_srt, safe_srt)
        
        subtitle_filter = f"subtitles={safe_srt}"
        
        command = [
            self.ffmpeg_path, '-i', self.video_path,
            '-t', '00:00:30',  # 30 second preview
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-crf', '23',
            '-preset', 'fast',
            '-y', preview_path
        ]
        
        def run_preview():
            try:
                subprocess.run(command, check=True, capture_output=True)
                messagebox.showinfo("Success", f"Preview created: {preview_path}")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to create preview: {e.stderr}")
            finally:
                # Clean up temp files
                if os.path.exists(temp_srt):
                    os.remove(temp_srt)
                if os.path.exists(safe_srt):
                    os.remove(safe_srt)
        
        import threading
        thread = threading.Thread(target=run_preview)
        thread.daemon = True
        thread.start()
    
    def apply_subtitles(self):
        """Apply subtitles to video"""
        if not self.subtitles:
            messagebox.showwarning("Warning", "No subtitles to apply")
            return
        
        # Save SRT file
        temp_srt = "temp_subtitles.srt"
        self.write_srt_file(temp_srt)
        
        # Ask for output file
        base_name = os.path.splitext(self.video_path)[0]
        output_path = filedialog.asksaveasfilename(
            title="Save Video with Subtitles",
            defaultextension=".mp4",
            initialfile=f"{base_name}_with_subtitles.mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        
        if output_path:
            # Use a different approach for Windows - copy subtitle file to avoid path issues
            import shutil
            safe_srt = "safe_subtitles.srt"
            shutil.copy2(temp_srt, safe_srt)
            
            # Use simpler filter syntax
            subtitle_filter = f"subtitles={safe_srt}"
            
            command = [
                self.ffmpeg_path, '-i', self.video_path,
                '-vf', subtitle_filter,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-crf', '23',
                '-preset', 'medium',
                '-y', output_path
            ]
            
            def run_apply():
                try:
                    subprocess.run(command, check=True, capture_output=True)
                    messagebox.showinfo("Success", f"Video with subtitles saved: {output_path}")
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error", f"Failed to apply subtitles: {e.stderr}")
                finally:
                    # Clean up temp files
                    if os.path.exists(temp_srt):
                        os.remove(temp_srt)
                    if os.path.exists(safe_srt):
                        os.remove(safe_srt)
            
            import threading
            thread = threading.Thread(target=run_apply)
            thread.daemon = True
            thread.start()

def main():
    """Main function"""
    root = tk.Tk()
    app = FFmpegDemoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
