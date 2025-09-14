#!/usr/bin/env python3
"""
FFmpeg Utility Functions
A collection of utility functions for video/audio processing using FFmpeg.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import speech_recognition as sr
from pydub import AudioSegment


class FFmpegUtils:
    def __init__(self, ffmpeg_path="ffmpeg"):
        """
        Initialize FFmpeg utilities.
        
        Args:
            ffmpeg_path (str): Path to ffmpeg executable. Defaults to "ffmpeg" (assumes it's in PATH).
        """
        self.ffmpeg_path = ffmpeg_path
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            subprocess.run([self.ffmpeg_path, '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try to find FFmpeg in common Windows locations
            common_paths = [
                "ffmpeg",  # In PATH
                "C:\\ffmpeg\\bin\\ffmpeg.exe",
                "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
                "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe",
                "C:\\tools\\ffmpeg\\bin\\ffmpeg.exe"
            ]
            
            for path in common_paths:
                try:
                    subprocess.run([path, '-version'], capture_output=True, check=True)
                    self.ffmpeg_path = path
                    print(f"Found FFmpeg at: {path}")
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            raise RuntimeError(f"FFmpeg not found. Please install FFmpeg or add it to your PATH. Tried paths: {common_paths}")
    
    def _run_command(self, command, description="FFmpeg operation"):
        """Run FFmpeg command and return result."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return {"success": True, "output": result.stdout, "error": result.stderr}
        except subprocess.CalledProcessError as e:
            return {"success": False, "output": e.stdout, "error": e.stderr}
    
    def trim_video(self, input_path, output_path, start_time, duration, precise=False, ultra_precise=False):
        """
        Trim video to specified duration.
        
        Args:5
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            start_time (str): Start time in HH:MM:SS format
            duration (str): Duration in HH:MM:SS format
            precise (bool): Use precise trimming with re-encoding
            ultra_precise (bool): Use ultra precise 2-pass trimming
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        if ultra_precise:
            return self._ultra_precise_trim(input_path, output_path, start_time, duration)
        elif precise:
            command = [
                self.ffmpeg_path, 
                '-ss', start_time,
                '-i', input_path,
                '-t', duration,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-crf', '23',
                '-preset', 'fast',
                '-avoid_negative_ts', 'make_zero',
                '-vsync', 'cfr',
                '-y', output_path
            ]
        else:
            # Fast trimming with copy
            command = [
                self.ffmpeg_path, '-i', input_path,
                '-ss', start_time,
                '-t', duration,
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                '-y', output_path
            ]
        
        return self._run_command(command, "Video Trimming")
    
    def _ultra_precise_trim(self, input_path, output_path, start_time, duration):
        """Ultra precise trimming using 2-pass approach."""
        temp_file = "temp_trim.mp4"
        
        try:
            # Parse time to add buffer
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
                '-crf', '23', '-preset', 'fast', '-y', temp_file
            ]
            
            result1 = self._run_command(command1, "Ultra Precise Trim Pass 1")
            if not result1["success"]:
                return result1
            
            # Second pass: Trim precisely from buffered segment
            offset_seconds = 1  # We added 1 second buffer at start
            offset_time = f"{offset_seconds//3600:02d}:{(offset_seconds%3600)//60:02d}:{offset_seconds%60:02d}"
            
            command2 = [
                self.ffmpeg_path, '-ss', offset_time, '-i', temp_file,
                '-t', duration, '-c:v', 'libx264', '-c:a', 'aac',
                '-crf', '23', '-preset', 'fast',
                '-avoid_negative_ts', 'make_zero', '-y', output_path
            ]
            
            result2 = self._run_command(command2, "Ultra Precise Trim Pass 2")
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return result2
            
        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return {"success": False, "error": str(e)}
    
    def convert_video(self, input_path, output_path, video_codec="libx264", audio_codec="aac", quality="23"):
        """
        Convert video format.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            video_codec (str): Video codec to use
            audio_codec (str): Audio codec to use
            quality (str): Quality setting (CRF value for libx264)
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            # Ensure even dimensions for yuv420p compatibility
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-c:v', video_codec,
            '-pix_fmt', 'yuv420p',
            '-profile:v', 'high',
            '-level', '4.1',
            '-movflags', '+faststart',
            '-c:a', audio_codec,
            '-crf', quality,
            '-preset', 'medium',
            '-y', output_path
        ]
        
        return self._run_command(command, "Video Conversion")
    
    def extract_audio(self, input_path, output_path, audio_codec="mp3", bitrate="192k"):
        """
        Extract audio from video.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output audio file
            audio_codec (str): Audio codec to use
            bitrate (str): Audio bitrate
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        command = [
            self.ffmpeg_path, '-i', input_path,
            '-vn',  # No video
            '-acodec', audio_codec,
            '-ab', bitrate,
            '-y', output_path
        ]
        
        return self._run_command(command, "Audio Extraction")
    
    def create_gif(self, input_path, output_path, start_time="00:00:00", duration="00:00:10", 
                   width=320, height=240):
        """
        Create GIF from video.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output GIF file
            start_time (str): Start time in HH:MM:SS format
            duration (str): Duration in HH:MM:SS format
            width (int): GIF width
            height (int): GIF height
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        palette_file = "temp_palette.png"
        
        try:
            # First generate palette
            palette_command = [
                self.ffmpeg_path, '-i', input_path,
                '-ss', start_time,
                '-t', duration,
                '-vf', f'scale={width}:{height}:flags=lanczos,palettegen',
                '-y', palette_file
            ]
            
            result1 = self._run_command(palette_command, "GIF Palette Generation")
            if not result1["success"]:
                return result1
            
            # Then create GIF
            gif_command = [
                self.ffmpeg_path, '-i', input_path,
                '-i', palette_file,
                '-ss', start_time,
                '-t', duration,
                '-filter_complex', f'[0:v]scale={width}:{height}:flags=lanczos[v];[v][1:v]paletteuse',
                '-y', output_path
            ]
            
            result2 = self._run_command(gif_command, "GIF Creation")
            
            # Clean up palette file
            if os.path.exists(palette_file):
                os.remove(palette_file)
            
            return result2
            
        except Exception as e:
            # Clean up palette file
            if os.path.exists(palette_file):
                os.remove(palette_file)
            return {"success": False, "error": str(e)}
    
    def get_media_info(self, input_path):
        """
        Get media file information.
        
        Args:
            input_path (str): Path to media file
            
        Returns:
            dict: Result with success status and media info or error message
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
        command = [
            ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
            input_path
        ]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            import json
            info = json.loads(result.stdout)
            return {"success": True, "info": info}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Failed to parse media info: {str(e)}"}
    
    def add_subtitles(self, input_path, output_path, subtitle_path, burn=False):
        """
        Add subtitles to video.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            subtitle_path (str): Path to subtitle file
            burn (bool): Whether to burn subtitles into video (hardcoded)
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        if not os.path.exists(subtitle_path):
            return {"success": False, "error": f"Subtitle file not found: {subtitle_path}"}
        
        if burn:
            # Burn subtitles into video
            safe_srt = "safe_burn_subtitles.srt"
            shutil.copy2(subtitle_path, safe_srt)
            
            subtitle_filter = f"subtitles={safe_srt}"
            command = [
                self.ffmpeg_path, '-i', input_path,
                '-vf', subtitle_filter,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-crf', '23',
                '-preset', 'medium',
                '-y', output_path
            ]
            
            result = self._run_command(command, "Burning Subtitles")
            
            # Clean up safe subtitle file
            if os.path.exists(safe_srt):
                os.remove(safe_srt)
            
            return result
        else:
            # Add soft subtitles
            command = [
                self.ffmpeg_path, '-i', input_path,
                '-i', subtitle_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-c:s', 'mov_text',
                '-map', '0:v',
                '-map', '0:a',
                '-map', '1:s',
                '-y', output_path
            ]
            
            return self._run_command(command, "Adding Subtitles")
    
    def add_background_music(self, input_path, output_path, music_path, volume=0.5, mix=True):
        """
        Add background music to video.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            music_path (str): Path to background music file
            volume (float): Volume level for background music (0.0 to 2.0)
            mix (bool): Whether to mix with original audio or replace it
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        if not os.path.exists(music_path):
            return {"success": False, "error": f"Music file not found: {music_path}"}
        
        if mix:
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
                '-shortest',
                '-y', output_path
            ]
        
        return self._run_command(command, "Adding Background Music")
    
    def add_sound_effect(self, input_path, output_path, effect_path, start_time=0, 
                        duration=None, volume=1.0, replace=False):
        """
        Add sound effect to video with timing controls.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            effect_path (str): Path to sound effect file
            start_time (float): Start time in seconds
            duration (float): Duration in seconds (None for full effect)
            volume (float): Volume level for effect
            replace (bool): Whether to replace original audio or mix with it
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        if not os.path.exists(effect_path):
            return {"success": False, "error": f"Effect file not found: {effect_path}"}
        
        command = [self.ffmpeg_path, '-i', input_path, '-i', effect_path]
        
        if replace:
            # Replace original audio with timed effect
            if start_time > 0 or duration:
                filter_steps = []
                
                if start_time > 0:
                    filter_steps.append(f"anullsrc=channel_layout=stereo:sample_rate=44100[silence]")
                    filter_steps.append(f"[silence]atrim=duration={start_time}[silence_trimmed]")
                
                effect_input = "[1:a]"
                if duration:
                    effect_input = f"[1:a]atrim=duration={duration}[effect_trimmed]"
                    filter_steps.append(effect_input)
                    effect_input = "[effect_trimmed]"
                
                filter_steps.append(f"{effect_input}volume={volume}[effect_vol]")
                
                if start_time > 0:
                    filter_steps.append(f"[silence_trimmed][effect_vol]concat=n=2:v=0:a=1[effect]")
                else:
                    filter_steps.append(f"[effect_vol]asplit[effect]")
                
                audio_filter = ";".join(filter_steps)
            else:
                audio_filter = f"[1:a]volume={volume}[effect]"
            
            command.extend(['-filter_complex', audio_filter, '-map', '0:v', '-map', '[effect]'])
        else:
            # Mix with original audio
            if start_time > 0 or duration:
                filter_steps = []
                
                if start_time > 0:
                    filter_steps.append(f"anullsrc=channel_layout=stereo:sample_rate=44100[silence]")
                    filter_steps.append(f"[silence]atrim=duration={start_time}[silence_trimmed]")
                
                effect_input = "[1:a]"
                if duration:
                    effect_input = f"[1:a]atrim=duration={duration}[effect_trimmed]"
                    filter_steps.append(effect_input)
                    effect_input = "[effect_trimmed]"
                
                filter_steps.append(f"{effect_input}volume={volume}[effect_vol]")
                
                if start_time > 0:
                    filter_steps.append(f"[silence_trimmed][effect_vol]concat=n=2:v=0:a=1[effect]")
                else:
                    filter_steps.append(f"[effect_vol]asplit[effect]")
                
                filter_steps.append(f"[0:a][effect]amix=inputs=2:duration=first:dropout_transition=3[out]")
                audio_filter = ";".join(filter_steps)
            else:
                audio_filter = f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=3:weights=1 {volume}[out]"
            
            command.extend(['-filter_complex', audio_filter, '-map', '0:v', '-map', '[out]'])
        
        command.extend(['-c:v', 'copy', '-c:a', 'aac', '-y', output_path])
        
        return self._run_command(command, "Adding Sound Effect")
    
    def apply_video_effects(self, input_path, output_path, blur=0, brightness=0, contrast=1, 
                           saturation=1, artistic_filter="none", zoom=False, rotation=0, 
                           horizontal_flip=False, vertical_flip=False, effects=None):
        """
        Apply video effects and filters.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            blur (float): Blur strength (0-10)
            brightness (float): Brightness adjustment (-1 to 1)
            contrast (float): Contrast adjustment (0-2)
            saturation (float): Saturation adjustment (0-2)
            artistic_filter (str): Artistic filter ("none", "black & white", "sepia", "vintage", "negative", "emboss", "edge detection")
            zoom (bool): Apply zoom effect
            rotation (float): Rotation in degrees
            horizontal_flip (bool): Horizontal flip
            vertical_flip (bool): Vertical flip
            effects (dict): Additional effects like {"speed": 2.0, "audio_tempo": 2.0}
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        filters = []
        audio_filters = []
        
        # Handle speed effects first (requires special handling)
        use_complex_speed = False
        speed_filterspec = None
        audio_filterspec = None
        if effects and "speed" in effects:
            try:
                speed = float(effects["speed"])
            except Exception:
                speed = 1.0
            if speed <= 0:
                speed = 1.0
            # Build explicit filter_complex specs to avoid setpts being ignored
            speed_filterspec = f"[0:v]setpts=PTS/{speed}[v]"
            tempo = float(effects.get("audio_tempo", speed))
            # Build atempo chain
            chain = []
            if 0.5 <= tempo <= 2.0:
                chain.append(f"atempo={tempo}")
            else:
                current = tempo
                while current > 2.0:
                    chain.append("atempo=2.0")
                    current /= 2.0
                while current < 0.5:
                    chain.append("atempo=0.5")
                    current *= 2.0
                if abs(current - 1.0) > 1e-6:
                    chain.append(f"atempo={current}")
            if chain:
                audio_filterspec = f"[0:a]{','.join(chain)}[a]"
            use_complex_speed = True
        
        # Basic effects
        if blur > 0:
            filters.append(f"gblur=sigma={blur}")
        
        # Handle additional effects from effects dict
        if effects:
            if "blur" in effects:
                filters.append(f"gblur=sigma={effects['blur']}")
            if "brightness" in effects:
                brightness = effects["brightness"]
            if "contrast" in effects:
                contrast = effects["contrast"]
            if "saturation" in effects:
                saturation = effects["saturation"]
        """
        Apply video effects and filters.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            blur (float): Blur strength (0-10)
            brightness (float): Brightness adjustment (-1 to 1)
            contrast (float): Contrast adjustment (0-2)
            saturation (float): Saturation adjustment (0-2)
            artistic_filter (str): Artistic filter ("none", "black & white", "sepia", "vintage", "negative", "emboss", "edge detection")
            zoom (bool): Apply zoom effect
            rotation (float): Rotation in degrees
            horizontal_flip (bool): Horizontal flip
            vertical_flip (bool): Vertical flip
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        filters = []
        
        # Basic effects
        if blur > 0:
            filters.append(f"gblur=sigma={blur}")
        
        # Artistic filters
        if artistic_filter == "vintage":
            if brightness != 0 or contrast != 1 or saturation != 1:
                final_brightness = brightness + 0.1
                final_contrast = contrast * 1.1
                final_saturation = saturation * 0.8
                filters.append(f"eq=brightness={final_brightness}:contrast={final_contrast}:saturation={final_saturation}")
            else:
                filters.append("eq=contrast=1.1:brightness=0.1:saturation=0.8")
            filters.append("colorbalance=rs=0.3:gs=-0.1:bs=-0.2")
        else:
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
        if zoom:
            filters.append("zoompan=z='min(zoom+0.0015,1.5)':d=25:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720")
        
        if rotation != 0:
            filters.append(f"rotate={rotation * 3.14159 / 180}")
        
        if horizontal_flip:
            filters.append("hflip")
        
        if vertical_flip:
            filters.append("vflip")
        
        # Build command
        command = [self.ffmpeg_path, '-y', '-i', input_path]
        
        if use_complex_speed:
            filterspecs = []
            if speed_filterspec:
                filterspecs.append(speed_filterspec)
            if audio_filterspec:
                filterspecs.append(audio_filterspec)
            command.extend(['-filter_complex', ';'.join(filterspecs)])
            # Map filtered streams
            if speed_filterspec:
                command.extend(['-map', '[v]'])
            else:
                command.extend(['-map', '0:v'])
            if audio_filterspec:
                command.extend(['-map', '[a]'])
            else:
                command.extend(['-map', '0:a?'])
            command.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        else:
            if filters:
                command.extend(['-vf', ','.join(filters)])
            if audio_filters:
                command.extend(['-af', ','.join(audio_filters)])
            video_codec_needed = bool(filters)
            audio_codec_needed = bool(audio_filters)
            if video_codec_needed and audio_codec_needed:
                command.extend(['-c:v', 'libx264', '-c:a', 'aac'])
            elif video_codec_needed:
                command.extend(['-c:v', 'libx264', '-c:a', 'copy'])
            elif audio_codec_needed:
                command.extend(['-c:v', 'copy', '-c:a', 'aac'])
            else:
                command.extend(['-c', 'copy'])
        
        command.append(output_path)
        
        return self._run_command(command, "Applying Video Effects")
    
    def transcribe_audio(self, input_path, output_path, language="en-US", chunk_duration=30):
        """
        Transcribe audio from video and generate subtitles automatically.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file with burned subtitles
            language (str): Language code for transcription
            chunk_duration (int): Duration of audio chunks in seconds
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        try:
            # Extract audio from video
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            extract_command = [
                self.ffmpeg_path, '-i', input_path,
                '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                '-y', temp_audio_path
            ]
            
            result = self._run_command(extract_command, "Audio Extraction")
            if not result["success"]:
                return result
            
            # Load audio file
            audio = AudioSegment.from_wav(temp_audio_path)
            
            # Initialize speech recognition
            recognizer = sr.Recognizer()
            
            # Split audio into chunks
            chunk_length = chunk_duration * 1000  # Convert to milliseconds
            chunks = [audio[i:i + chunk_length] for i in range(0, len(audio), chunk_length)]
            
            # Transcribe each chunk
            subtitles = []
            for i, chunk in enumerate(chunks):
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
                            
                            # Split text into natural speech chunks
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
                                        
                                        # Ensure minimum and maximum duration
                                        min_duration = 1.0
                                        max_duration = 8.0
                                        
                                        actual_duration = subtitle_end - subtitle_start
                                        if actual_duration < min_duration:
                                            subtitle_end = subtitle_start + min_duration
                                        elif actual_duration > max_duration:
                                            subtitle_end = subtitle_start + max_duration
                                        
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
                    return {"success": False, "error": f"Speech recognition service error: {e}"}
                finally:
                    # Clean up chunk file
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
            
            # Generate SRT file
            base_name = os.path.splitext(input_path)[0]
            srt_path = f"{base_name}_transcribed.srt"
            
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                for i, subtitle in enumerate(subtitles, 1):
                    start_time_str = self._format_srt_time(subtitle['start'])
                    end_time_str = self._format_srt_time(subtitle['end'])
                    srt_file.write(f"{i}\n")
                    srt_file.write(f"{start_time_str} --> {end_time_str}\n")
                    srt_file.write(f"{subtitle['text']}\n\n")
            
            # Burn subtitles into video
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
            
            result = self._run_command(burn_command, "Burning Subtitles")
            
            # Clean up files
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            if os.path.exists(safe_srt):
                os.remove(safe_srt)
            if os.path.exists(srt_path):
                os.remove(srt_path)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _format_srt_time(self, seconds):
        """Format seconds into SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _split_into_speech_chunks(self, text):
        """Split text into natural speech chunks based on punctuation and pauses."""
        import re
        
        # First, split by major punctuation
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
    
    def splice_video(self, input_path, output_path, remove_start_time, remove_end_time):
        """
        Splice/cut out a section of video by removing the specified time range.
        Uses re-encoding to ensure proper synchronization and avoid corruption.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            remove_start_time (str): Start time of section to remove (HH:MM:SS format)
            remove_end_time (str): End time of section to remove (HH:MM:SS format)
            
        Returns:
            dict: Result with success status and output/error messages
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        try:
            # Convert time strings to seconds for calculations
            def time_to_seconds(time_str):
                parts = time_str.split(':')
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            
            def seconds_to_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            
            remove_start_seconds = time_to_seconds(remove_start_time)
            remove_end_seconds = time_to_seconds(remove_end_time)
            
            # Get video duration first
            info_result = self.get_media_info(input_path)
            if not info_result["success"]:
                return {"success": False, "error": "Could not get video duration"}
            
            total_duration_seconds = float(info_result["info"]["format"]["duration"])
            
            print(f"🔧 Splice operation details:")
            print(f"   Total duration: {total_duration_seconds:.2f}s")
            print(f"   Remove from: {remove_start_seconds}s to {remove_end_seconds}s")
            print(f"   Remove duration: {remove_end_seconds - remove_start_seconds:.2f}s")
            
            # Create temporary files for the parts
            temp_part1 = "temp_splice_part1.mp4"
            temp_part2 = "temp_splice_part2.mp4"
            temp_concat = "temp_splice_concat.txt"
            
            parts_to_concat = []
            
            try:
                # Part 1: From beginning to remove_start_time (if exists)
                if remove_start_seconds > 1:  # Only if there's more than 1 second before
                    print(f"🔧 Creating part 1: 0s to {remove_start_seconds}s")
                    
                    command1 = [
                        self.ffmpeg_path, '-i', input_path,
                        '-t', seconds_to_time(remove_start_seconds),
                        '-c:v', 'libx264', '-c:a', 'aac',
                        '-crf', '23', '-preset', 'fast',
                        '-avoid_negative_ts', 'make_zero',
                        '-y', temp_part1
                    ]
                    
                    result1 = self._run_command(command1, "Extracting Part 1")
                    if result1["success"]:
                        parts_to_concat.append(temp_part1)
                        print(f"✅ Part 1 created successfully")
                    else:
                        print(f"❌ Error creating part 1: {result1['error']}")
                        return result1
                
                # Part 2: From remove_end_time to end (if exists)
                if remove_end_seconds < total_duration_seconds - 1:  # Only if there's more than 1 second after
                    remaining_duration = total_duration_seconds - remove_end_seconds
                    print(f"🔧 Creating part 2: {remove_end_seconds}s to end ({remaining_duration:.2f}s)")
                    
                    command2 = [
                        self.ffmpeg_path, '-ss', remove_end_time, '-i', input_path,
                        '-c:v', 'libx264', '-c:a', 'aac',
                        '-crf', '23', '-preset', 'fast',
                        '-avoid_negative_ts', 'make_zero',
                        '-y', temp_part2
                    ]
                    
                    result2 = self._run_command(command2, "Extracting Part 2")
                    if result2["success"]:
                        parts_to_concat.append(temp_part2)
                        print(f"✅ Part 2 created successfully")
                    else:
                        print(f"❌ Error creating part 2: {result2['error']}")
                        return result2
                
                # Check if we have parts to concatenate
                if len(parts_to_concat) == 0:
                    return {"success": False, "error": "Nothing to splice - the entire video would be removed"}
                
                print(f"🔧 Parts to concatenate: {len(parts_to_concat)}")
                for i, part in enumerate(parts_to_concat):
                    if os.path.exists(part):
                        size = os.path.getsize(part) / (1024*1024)
                        print(f"   Part {i+1}: {part} ({size:.2f} MB)")
                
                # Concatenate parts if we have more than one
                if len(parts_to_concat) > 1:
                    # Create concat file with absolute paths
                    with open(temp_concat, 'w') as f:
                        for part in parts_to_concat:
                            f.write(f"file '{os.path.abspath(part)}'\n")
                    
                    print(f"📝 Concat file contents:")
                    with open(temp_concat, 'r') as f:
                        print(f.read())
                    
                    command3 = [
                        self.ffmpeg_path, '-f', 'concat', '-safe', '0',
                        '-i', temp_concat,
                        '-c:v', 'libx264', '-c:a', 'aac',
                        '-crf', '23', '-preset', 'fast',
                        '-avoid_negative_ts', 'make_zero',
                        '-fflags', '+genpts',
                        '-y', output_path
                    ]
                    
                    print(f"🔧 Running concat command...")
                    result3 = self._run_command(command3, "Concatenating Parts")
                    
                elif len(parts_to_concat) == 1:
                    # Only one part - just copy it as the final result
                    print(f"🔧 Only one part exists, copying as final result...")
                    import shutil
                    shutil.copy2(parts_to_concat[0], output_path)
                    result3 = {"success": True, "output": "Single part copied successfully"}
                
                # Clean up temporary files
                for temp_file in [temp_part1, temp_part2, temp_concat]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
                return result3
                
            except Exception as e:
                # Clean up temporary files on error
                for temp_file in [temp_part1, temp_part2, temp_concat]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                return {"success": False, "error": str(e)}
                
        except Exception as e:
            return {"success": False, "error": f"Splice error: {str(e)}"}


# Convenience functions for quick usage
def trim_video(input_path, output_path, start_time, duration, precise=False, ultra_precise=False, ffmpeg_path="ffmpeg"):
    """Quick function to trim video."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.trim_video(input_path, output_path, start_time, duration, precise, ultra_precise)

def convert_video(input_path, output_path, video_codec="libx264", audio_codec="aac", quality="23", ffmpeg_path="ffmpeg"):
    """Quick function to convert video."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.convert_video(input_path, output_path, video_codec, audio_codec, quality)

def extract_audio(input_path, output_path, audio_codec="mp3", bitrate="192k", ffmpeg_path="ffmpeg"):
    """Quick function to extract audio."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.extract_audio(input_path, output_path, audio_codec, bitrate)

def create_gif(input_path, output_path, start_time="00:00:00", duration="00:00:10", 
               width=320, height=240, ffmpeg_path="ffmpeg"):
    """Quick function to create GIF."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.create_gif(input_path, output_path, start_time, duration, width, height)

def get_media_info(input_path, ffmpeg_path="ffmpeg"):
    """Quick function to get media info."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.get_media_info(input_path)

def add_subtitles(input_path, output_path, subtitle_path, burn=False, ffmpeg_path="ffmpeg"):
    """Quick function to add subtitles."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.add_subtitles(input_path, output_path, subtitle_path, burn)

def add_background_music(input_path, output_path, music_path, volume=0.5, mix=True, ffmpeg_path="ffmpeg"):
    """Quick function to add background music."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.add_background_music(input_path, output_path, music_path, volume, mix)

def add_sound_effect(input_path, output_path, effect_path, start_time=0, duration=None, 
                    volume=1.0, replace=False, ffmpeg_path="ffmpeg"):
    """Quick function to add sound effect."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.add_sound_effect(input_path, output_path, effect_path, start_time, duration, volume, replace)

def apply_video_effects(input_path, output_path, blur=0, brightness=0, contrast=1, saturation=1, 
                       artistic_filter="none", zoom=False, rotation=0, horizontal_flip=False, 
                       vertical_flip=False, ffmpeg_path="ffmpeg"):
    """Quick function to apply video effects."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.apply_video_effects(input_path, output_path, blur, brightness, contrast, saturation,
                                   artistic_filter, zoom, rotation, horizontal_flip, vertical_flip)

def transcribe_audio(input_path, output_path, language="en-US", chunk_duration=30, ffmpeg_path="ffmpeg"):
    """Quick function to transcribe audio."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.transcribe_audio(input_path, output_path, language, chunk_duration)

def splice_video(input_path, output_path, remove_start_time, remove_end_time, ffmpeg_path="ffmpeg"):
    """Quick function to splice/cut out a section of video."""
    utils = FFmpegUtils(ffmpeg_path)
    return utils.splice_video(input_path, output_path, remove_start_time, remove_end_time)