<<<<<<< HEAD
# FFmpeg Demo Application

A comprehensive GUI application built with Python and Tkinter that showcases various FFmpeg capabilities for video and audio processing.

## Features

### Video Processing
- **Format Conversion**: Convert between MP4, AVI, MOV, MKV, WebM, and GIF formats
- **Video Trimming**: Cut videos to specific time ranges
- **Video Scaling**: Resize videos to custom dimensions
- **Quality Control**: Adjust video quality using CRF (Constant Rate Factor)
- **GIF Creation**: Convert video segments to animated GIFs
- **Watermarking**: Add text watermarks to videos
- **Slideshow Creation**: Create videos from image sequences

### Audio Processing
- **Audio Extraction**: Extract audio from video files
- **Format Conversion**: Convert between MP3, WAV, AAC, FLAC, and OGG
- **Bitrate Control**: Adjust audio quality and file size

### Advanced Features
- **Media Information**: Display detailed information about media files
- **Batch Processing**: Process multiple files
- **Custom Filters**: Apply custom FFmpeg filters
- **Progress Tracking**: Real-time progress indication
- **Error Handling**: Comprehensive error reporting

## Prerequisites

### 1. Install FFmpeg
FFmpeg must be installed and available in your system PATH.

#### Windows:
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract the files to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system PATH
4. Verify installation by running `ffmpeg -version` in command prompt

#### macOS:
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

## Installation

1. Clone or download this repository
2. Install FFmpeg (see Prerequisites)
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application
```bash
python ffmpeg_demo.py
```

### Creating Sample Media Files
To create sample video and audio files for testing:
```bash
python create_samples.py
```

This will create sample files in the `samples/` directory.

### Using the GUI

1. **File Selection**: Click "Browse" to select input and output files
2. **Video Processing**: 
   - Choose output format
   - Set start time and duration for trimming
   - Adjust scale dimensions
   - Set quality (CRF value)
3. **Audio Processing**: Select audio codec and bitrate
4. **Advanced Options**: Choose video codec and add custom filters
5. **Execute**: Click the appropriate processing button

### Available Operations

- **Convert Video**: Convert between different video formats
- **Trim Video**: Cut video to specific time range
- **Extract Audio**: Extract audio track from video
- **Create GIF**: Convert video segment to animated GIF
- **Get Info**: Display detailed media file information

## File Structure

```
FFmpeg-Demo/
├── ffmpeg_demo.py          # Main GUI application
├── media_utils.py          # Utility functions for media processing
├── create_samples.py       # Script to create sample media files
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── samples/               # Sample media files (created by create_samples.py)
    ├── sample_short.mp4
    ├── sample_hd.mp4
    ├── sample_small.mp4
    ├── sample_audio_short.wav
    └── sample_audio_long.wav
```

## Technical Details

### Dependencies
- **tkinter**: GUI framework (included with Python)
- **Pillow**: Image processing
- **ffmpeg-python**: Python wrapper for FFmpeg
- **opencv-python**: Computer vision library for video processing
- **numpy**: Numerical computing

### Supported Formats

#### Video Formats:
- MP4 (H.264, H.265)
- AVI
- MOV
- MKV
- WebM (VP8, VP9)
- GIF

#### Audio Formats:
- MP3
- WAV
- AAC
- FLAC
- OGG

### Quality Settings

- **CRF (Constant Rate Factor)**: 0-51 scale
  - 0 = Lossless
  - 18-23 = High quality
  - 28-35 = Medium quality
  - 51 = Lowest quality

- **Audio Bitrates**: 64k, 128k, 192k, 256k, 320k

## Troubleshooting

### Common Issues

1. **"FFmpeg not found" error**:
   - Ensure FFmpeg is installed and in your system PATH
   - Test by running `ffmpeg -version` in terminal

2. **Permission errors**:
   - Ensure you have write permissions in the output directory
   - Try running as administrator (Windows) or with sudo (Linux/macOS)

3. **Memory issues with large files**:
   - Use lower quality settings
   - Process shorter segments
   - Ensure sufficient disk space

4. **Unsupported format errors**:
   - Check if the input format is supported
   - Try converting to a common format first

### Performance Tips

- Use "copy" codec for trimming to avoid re-encoding
- Lower quality settings for faster processing
- Process shorter segments for testing
- Use SSD storage for better performance

## Examples

### Convert MP4 to WebM
1. Select input MP4 file
2. Set output file with .webm extension
3. Choose "libvpx-vp9" codec in advanced options
4. Click "Convert Video"

### Create a 10-second GIF
1. Select input video
2. Set start time (e.g., "00:00:05")
3. Set duration to "00:00:10"
4. Adjust scale dimensions
5. Click "Create GIF"

### Extract Audio from Video
1. Select input video file
2. Click "Extract Audio"
3. Audio will be saved as MP3

## Contributing

Feel free to contribute by:
- Adding new features
- Improving error handling
- Adding support for more formats
- Optimizing performance
- Improving the GUI

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Ensure FFmpeg is properly installed
3. Verify file formats are supported
4. Check system requirements

---

**Note**: This application requires FFmpeg to be installed on your system. The application provides a user-friendly interface for common FFmpeg operations but does not include FFmpeg itself.
=======
# video-cursor
>>>>>>> 8b6cff7ec4fd156dd521f14f50829b2587a8d37d
