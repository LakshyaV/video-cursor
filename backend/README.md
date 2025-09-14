# Professional AI-Powered Video Editor

A comprehensive video editing platform powered by Python FastAPI backend with advanced AI capabilities including natural language processing, object detection, and automated video analysis.

## 🚀 Quick Start

1. **Install and run:**
   ```bash
   chmod +x ../start.sh
   ../start.sh
   ```

2. **Access the application:**
   - Frontend: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

## 🎯 Features

### Complete Video Editing
- Video processing (trim, splice, effects)
- Audio management (extract, background music)
- Subtitle generation and transcription
- Format conversion and GIF creation

### AI-Powered Capabilities
- Natural language video editing commands
- Automatic vague/specific request analysis
- Video content search and summarization
- Object detection and tracking

### Professional Interface
- DaVinci Resolve-style UI
- Real-time preview and feedback
- File management and organization

## 🛠 Technology Stack

- **FastAPI**: High-performance Python web framework
- **FFmpeg**: Professional video processing
- **Cohere AI**: Natural language processing
- **TwelveLabs**: Video understanding and search
- **OpenCV**: Computer vision and object detection

## 📋 API Endpoints

All functionality is accessible via REST API:

- **File Management**: Upload, list, delete files
- **Video Processing**: Trim, splice, effects, conversion
- **AI Features**: Natural language editing, analysis
- **Object Detection**: Track and modify objects
- **Export**: Download and preview processed videos

## 🔧 Configuration

Set up your API keys in `.env`:
```bash
COHERE_API_KEY=your_cohere_api_key
api_key_1=your_twelvelabs_api_key
```

## 🏗 Architecture

The backend integrates all video editing functionality:
- `server.py`: Main FastAPI application with all endpoints
- `utils.py`: FFmpeg wrapper for video processing
- `object.py`: Computer vision and object detection
- `specific.py`: AI-powered command extraction
- `vague.py`: Natural language processing
- `output_utils.py`: File management utilities

**Node.js completely replaced with Python FastAPI for all backend functionality.**
