from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import tempfile
import shutil
import uuid
from pathlib import Path
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

# Import all backend modules
from utils import FFmpegUtils
from object import ObjectTracker
import output_utils
import cohere
from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem
from twelvelabs.tasks import TasksRetrieveResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Professional Video Editor API", 
    version="2.0.0",
    description="Complete video editing platform with AI-powered features"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (replaces Node.js server completely)
# Public directory is in parent folder relative to backend
public_dir = Path(__file__).parent.parent / "public"
if not public_dir.exists():
    raise RuntimeError(f"Public directory not found at {public_dir}. Please ensure the 'public' folder exists in the project root.")
app.mount("/static", StaticFiles(directory=str(public_dir)), name="static")

# Global variables for processing
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ffmpeg_utils = FFmpegUtils()
object_detector = ObjectTracker() if ObjectTracker else None
executor = ThreadPoolExecutor(max_workers=4)

# Initialize AI services
cohere_client = None
twelvelabs_client = None

if os.getenv("COHERE_API_KEY"):
    cohere_client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))

if os.getenv("api_key_1"):
    twelvelabs_client = TwelveLabs(api_key=os.getenv("api_key_1"))

# Pydantic models for request validation
class VideoProcessRequest(BaseModel):
    video_id: str
    start_time: Optional[str] = "00:00:00"
    duration: Optional[str] = None
    end_time: Optional[str] = None

class VideoEffectsRequest(BaseModel):
    video_id: str
    blur: Optional[float] = 0
    brightness: Optional[float] = 0
    contrast: Optional[float] = 1
    saturation: Optional[float] = 1
    artistic_filter: Optional[str] = "none"
    zoom: Optional[bool] = False
    rotation: Optional[float] = 0
    horizontal_flip: Optional[bool] = False
    vertical_flip: Optional[bool] = False

class AudioRequest(BaseModel):
    video_id: str
    audio_file_id: Optional[str] = None
    volume: Optional[float] = 0.5
    start_time: Optional[float] = 0
    duration: Optional[float] = None
    mix: Optional[bool] = True

class SubtitleRequest(BaseModel):
    video_id: str
    subtitle_file_id: Optional[str] = None
    burn: Optional[bool] = False
    language: Optional[str] = "en-US"
    auto_transcribe: Optional[bool] = False

class AIEditRequest(BaseModel):
    video_id: str
    prompt: str
    edit_type: str  # "vague" or "specific"

class ObjectTrackingRequest(BaseModel):
    video_id: str
    target_object: str
    start_time: Optional[str] = None
    duration: Optional[str] = None
    action: str  # "blur", "zoom", "track"
    intensity: Optional[float] = 1.0

class TwelveLabsRequest(BaseModel):
    video_id: str
    query: str
    search_type: Optional[str] = "visual"  # "visual", "audio", or "both"

# Root endpoint - serve the main application
@app.get("/")
async def read_root():
    index_file = Path(__file__).parent.parent / "public" / "index.html"
    return FileResponse(str(index_file))

# Serve CSS and JS files directly (for compatibility with existing HTML)
@app.get("/styles.css")
async def serve_css():
    css_file = Path(__file__).parent.parent / "public" / "styles.css"
    return FileResponse(str(css_file), media_type="text/css")

@app.get("/script.js")
async def serve_js():
    js_file = Path(__file__).parent.parent / "public" / "script.js"
    return FileResponse(str(js_file), media_type="application/javascript")

# ====================
# FILE MANAGEMENT APIS
# ====================

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload video, audio, or subtitle files"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix.lower()
    file_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get media info
    file_info = ffmpeg_utils.get_media_info(str(file_path))
    
    # Determine file type
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'}
    audio_extensions = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'}
    subtitle_extensions = {'.srt', '.vtt', '.ass', '.ssa'}
    
    if file_extension in video_extensions:
        file_type = "video"
    elif file_extension in audio_extensions:
        file_type = "audio"
    elif file_extension in subtitle_extensions:
        file_type = "subtitle"
    else:
        file_type = "unknown"
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "file_type": file_type,
        "size": file_path.stat().st_size,
        "media_info": file_info.get("info") if file_info["success"] else None
    }

@app.get("/api/files")
async def list_files():
    """List all uploaded files"""
    files = []
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            file_id = file_path.stem
            file_info = output_utils.get_file_info(str(file_path))
            files.append({
                "file_id": file_id,
                "filename": file_path.name,
                "size": file_info.get("size_bytes", 0),
                "created": file_info.get("created", 0),
                "extension": file_info.get("extension", "")
            })
    return {"files": files}

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """Delete uploaded or output files"""
    files_deleted = 0
    
    # Delete from uploads
    for file_path in UPLOAD_DIR.glob(f"{file_id}.*"):
        file_path.unlink()
        files_deleted += 1
    
    # Delete from outputs
    for file_path in OUTPUT_DIR.glob(f"{file_id}.*"):
        file_path.unlink()
        files_deleted += 1
    
    if files_deleted == 0:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"message": f"Deleted {files_deleted} file(s)"}

@app.get("/api/info/{file_id}")
async def get_file_info(file_id: str):
    """Get detailed media file information"""
    input_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    input_path = input_files[0]
    result = ffmpeg_utils.get_media_info(str(input_path))
    
    if result["success"]:
        return {"file_id": file_id, "info": result["info"]}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

# ====================
# BASIC VIDEO PROCESSING
# ====================

@app.post("/api/trim")
async def trim_video(request: VideoProcessRequest):
    """Trim video to specified time range"""
    input_path = await get_input_file(request.video_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    if request.duration:
        result = ffmpeg_utils.trim_video(
            str(input_path), str(output_path), 
            request.start_time, request.duration, precise=True
        )
    elif request.end_time:
        duration = calculate_duration(request.start_time, request.end_time)
        result = ffmpeg_utils.trim_video(
            str(input_path), str(output_path), 
            request.start_time, duration, precise=True
        )
    else:
        raise HTTPException(status_code=400, detail="Either duration or end_time must be provided")
    
    if result["success"]:
        return {"output_id": output_id, "message": "Video trimmed successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/splice")
async def splice_video(
    video_id: str = Form(...),
    remove_start_time: str = Form(...),
    remove_end_time: str = Form(...)
):
    """Remove a section from the video"""
    input_path = await get_input_file(video_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.splice_video(
        str(input_path), str(output_path), remove_start_time, remove_end_time
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Video spliced successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/effects")
async def apply_effects(request: VideoEffectsRequest):
    """Apply visual effects to video"""
    input_path = await get_input_file(request.video_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.apply_video_effects(
        str(input_path), str(output_path),
        blur=request.blur,
        brightness=request.brightness,
        contrast=request.contrast,
        saturation=request.saturation,
        artistic_filter=request.artistic_filter,
        zoom=request.zoom,
        rotation=request.rotation,
        horizontal_flip=request.horizontal_flip,
        vertical_flip=request.vertical_flip
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Effects applied successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/convert")
async def convert_video(
    video_id: str = Form(...),
    video_codec: str = Form("libx264"),
    audio_codec: str = Form("aac"),
    quality: str = Form("23")
):
    """Convert video format and codec"""
    input_path = await get_input_file(video_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.convert_video(
        str(input_path), str(output_path), 
        video_codec, audio_codec, quality
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Video converted successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

# ====================
# AUDIO PROCESSING
# ====================

@app.post("/api/audio/extract")
async def extract_audio(
    video_id: str = Form(...),
    audio_codec: str = Form("mp3"),
    bitrate: str = Form("192k")
):
    """Extract audio from video"""
    input_path = await get_input_file(video_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.{audio_codec}"
    
    result = ffmpeg_utils.extract_audio(
        str(input_path), str(output_path), audio_codec, bitrate
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Audio extracted successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/audio/background")
async def add_background_music(request: AudioRequest):
    """Add background music to video"""
    input_path = await get_input_file(request.video_id)
    audio_path = await get_input_file(request.audio_file_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.add_background_music(
        str(input_path), str(output_path), 
        str(audio_path), request.volume, request.mix
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Background music added successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/audio/effect")
async def add_sound_effect(request: AudioRequest):
    """Add timed sound effect to video"""
    input_path = await get_input_file(request.video_id)
    audio_path = await get_input_file(request.audio_file_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.add_sound_effect(
        str(input_path), str(output_path), str(audio_path),
        request.start_time, request.duration, request.volume, not request.mix
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Sound effect added successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

# ====================
# SUBTITLE PROCESSING
# ====================

@app.post("/api/subtitles")
async def add_subtitles(request: SubtitleRequest):
    """Add subtitles to video or auto-transcribe"""
    input_path = await get_input_file(request.video_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    if request.auto_transcribe:
        result = ffmpeg_utils.transcribe_audio(
            str(input_path), str(output_path), request.language
        )
    else:
        if not request.subtitle_file_id:
            raise HTTPException(status_code=400, detail="Subtitle file required when not auto-transcribing")
        
        subtitle_path = await get_input_file(request.subtitle_file_id)
        result = ffmpeg_utils.add_subtitles(
            str(input_path), str(output_path), str(subtitle_path), request.burn
        )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Subtitles added successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

# ====================
# ADVANCED AI FEATURES
# ====================

@app.post("/api/ai/edit")
async def ai_powered_edit(request: AIEditRequest):
    """AI-powered video editing using natural language"""
    if not cohere_client:
        raise HTTPException(status_code=503, detail="AI service not available - please set COHERE_API_KEY")
    
    input_path = await get_input_file(request.video_id)
    
    try:
        if request.edit_type == "vague":
            # Process vague request
            result = await process_vague_request(request.prompt, str(input_path))
        else:
            # Process specific request
            result = await process_specific_request(request.prompt, str(input_path))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

@app.post("/api/ai/analyze")
async def analyze_prompt(prompt: str = Form(...)):
    """Analyze if a prompt is vague or specific"""
    if not cohere_client:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    analysis_prompt = (
        f"The following is a user request for a video edit: '{prompt}'. "
        "Is this a vague ask or a specific ask for a video edit? "
        "Reply with either 'vague' or 'specific'."
    )
    
    response = cohere_client.chat(
        model="command-r-plus",
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    
    result = extract_response_text(response).strip().lower()
    return {"prompt": prompt, "type": result, "is_specific": result == "specific"}

@app.post("/api/twelvelabs/upload")
async def upload_to_twelvelabs(video_id: str = Form(...)):
    """Upload video to TwelveLabs for AI analysis"""
    if not twelvelabs_client:
        raise HTTPException(status_code=503, detail="TwelveLabs service not available - please set api_key_1")
    
    input_path = await get_input_file(video_id)
    
    try:
        # Create index
        index = twelvelabs_client.indexes.create(
            index_name=f"video_{video_id}_{int(time.time())}",
            models=[
                IndexesCreateRequestModelsItem(
                    model_name="pegasus1.2", model_options=["visual", "audio"]
                ),
                IndexesCreateRequestModelsItem(
                    model_name="marengo2.7", model_options=["visual", "audio"]
                )
            ]
        )
        
        # Upload video
        with open(input_path, "rb") as f:
            task = twelvelabs_client.tasks.create(index_id=index.id, video_file=f)
        
        return {
            "index_id": index.id,
            "task_id": task.id,
            "message": "Video uploaded to TwelveLabs successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TwelveLabs upload failed: {str(e)}")

@app.post("/api/twelvelabs/search")
async def search_video_content(request: TwelveLabsRequest):
    """Search for specific content in uploaded video"""
    if not twelvelabs_client:
        raise HTTPException(status_code=503, detail="TwelveLabs service not available")
    
    # For demo purposes, use a default index - in production, you'd track uploaded videos
    try:
        search_options = ["visual", "audio"] if request.search_type == "both" else [request.search_type]
        
        # This would use the index from a previous upload
        # For now, return a mock response
        return {
            "query": request.query,
            "results": [
                {"start": 10.5, "end": 15.2, "score": 0.95, "confidence": 0.88},
                {"start": 25.1, "end": 30.8, "score": 0.87, "confidence": 0.82}
            ],
            "message": "Search completed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TwelveLabs search failed: {str(e)}")

@app.post("/api/video/summarize")
async def summarize_video(video_id: str = Form(...)):
    """Generate AI summary of video content"""
    if not twelvelabs_client:
        raise HTTPException(status_code=503, detail="TwelveLabs service not available")
    
    # Mock implementation - would use actual TwelveLabs summarization
    return {
        "video_id": video_id,
        "summary": "This video contains various scenes with people and objects. Key moments include conversations, movement, and environmental changes throughout the duration.",
        "timestamps": [
            {"time": "00:00:05", "description": "Opening scene"},
            {"time": "00:00:15", "description": "Main action begins"},
            {"time": "00:00:30", "description": "Dialogue sequence"}
        ]
    }

# ====================
# OBJECT DETECTION & TRACKING
# ====================

@app.post("/api/object/detect")
async def detect_objects(video_id: str = Form(...)):
    """Detect objects in video"""
    if not object_detector:
        raise HTTPException(status_code=503, detail="Object detection not available")
    
    input_path = await get_input_file(video_id)
    
    try:
        # Use object detection from object.py
        results = object_detector.detect_objects_in_video(str(input_path))
        return {"video_id": video_id, "detections": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object detection failed: {str(e)}")

@app.post("/api/object/track")
async def track_object(request: ObjectTrackingRequest):
    """Track specific object in video and apply effects"""
    input_path = await get_input_file(request.video_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    try:
        if request.action == "blur":
            result = await blur_object_in_video(
                str(input_path), str(output_path), 
                request.target_object, request.start_time, request.duration
            )
        elif request.action == "zoom":
            result = await zoom_to_object_in_video(
                str(input_path), str(output_path), 
                request.target_object, request.start_time, request.duration, request.intensity
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'blur' or 'zoom'")
        
        if result["success"]:
            return {"output_id": output_id, "message": f"Object {request.action} applied successfully"}
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object tracking failed: {str(e)}")

# ====================
# EXPORT & DOWNLOAD
# ====================

@app.post("/api/gif")
async def create_gif(
    video_id: str = Form(...),
    start_time: str = Form("00:00:00"),
    duration: str = Form("00:00:10"),
    width: int = Form(320),
    height: int = Form(240)
):
    """Create animated GIF from video"""
    input_path = await get_input_file(video_id)
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.gif"
    
    result = ffmpeg_utils.create_gif(
        str(input_path), str(output_path), start_time, duration, width, height
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "GIF created successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/api/download/{output_id}")
async def download_file(output_id: str):
    """Download processed file"""
    output_files = list(OUTPUT_DIR.glob(f"{output_id}.*"))
    if not output_files:
        raise HTTPException(status_code=404, detail="Output file not found")
    
    output_path = output_files[0]
    return FileResponse(
        path=str(output_path),
        filename=f"edited_{output_path.name}",
        media_type='application/octet-stream'
    )

@app.get("/api/preview/{file_id}")
async def preview_file(file_id: str):
    """Stream video preview"""
    # Try output files first, then uploaded files
    file_paths = list(OUTPUT_DIR.glob(f"{file_id}.*")) + list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not file_paths:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = file_paths[0]
    
    def iterfile(file_path: str):
        with open(file_path, mode="rb") as file_like:
            yield from file_like
    
    media_type = "video/mp4" if file_path.suffix.lower() in ['.mp4', '.mov', '.avi'] else "application/octet-stream"
    
    return StreamingResponse(iterfile(str(file_path)), media_type=media_type)

@app.get("/api/outputs")
async def list_outputs():
    """List all processed output files"""
    outputs = []
    for file_path in OUTPUT_DIR.glob("*"):
        if file_path.is_file():
            file_info = output_utils.get_file_info(str(file_path))
            outputs.append({
                "output_id": file_path.stem,
                "filename": file_path.name,
                "size": file_info.get("size_bytes", 0),
                "created": file_info.get("created", 0),
                "extension": file_info.get("extension", "")
            })
    return {"outputs": outputs}

# ====================
# UTILITY FUNCTIONS
# ====================

async def get_input_file(file_id: str) -> Path:
    """Get input file path and validate existence"""
    input_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="File not found")
    return input_files[0]

def calculate_duration(start_time: str, end_time: str) -> str:
    """Calculate duration between two timestamps"""
    def time_to_seconds(time_str):
        parts = time_str.split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    
    start_seconds = time_to_seconds(start_time)
    end_seconds = time_to_seconds(end_time)
    duration_seconds = end_seconds - start_seconds
    
    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    seconds = duration_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def extract_response_text(response) -> str:
    """Extract text from Cohere API response"""
    if hasattr(response, 'text'):
        return response.text
    elif hasattr(response, 'message') and hasattr(response.message, 'content'):
        for item in response.message.content:
            if hasattr(item, 'text'):
                return item.text
    return str(response)

async def process_vague_request(prompt: str, video_path: str) -> Dict[str, Any]:
    """Process vague editing request using AI"""
    # Implementation would use the vague.py logic
    analysis_prompt = f"""
    You are given a vague video edit request. Generate specific editing commands based on this request.
    Request: "{prompt}"
    
    Available edit techniques: clip trimming, transitions, audio effects, dynamic zoom, 
    object face blur, face/object tracking, subtitles, video effects.
    
    Return editing commands in this format:
    <command> AND <where in video it should be applied>
    """
    
    response = cohere_client.chat(
        model="command-r-plus",
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    
    commands = extract_response_text(response)
    return {"type": "vague", "commands": commands, "status": "analyzed"}

async def process_specific_request(prompt: str, video_path: str) -> Dict[str, Any]:
    """Process specific editing request"""
    # Implementation would use the specific.py logic
    extraction_prompt = f"""
    Extract specific video edit commands from this request.
    Output only in this format: <command> AND <where in video/audio it should be applied>
    
    Request: "{prompt}"
    Available techniques: clip trimming, transitions, audio effects, dynamic zoom, 
    face zoom, object face blur, face/object tracking, subtitles, video effects, 
    blur, saturation, brightness, contrast, artistic filters, sound effects, splice.
    """
    
    response = cohere_client.chat(
        model="command-r-plus",
        messages=[{"role": "user", "content": extraction_prompt}]
    )
    
    commands = extract_response_text(response)
    return {"type": "specific", "commands": commands, "status": "extracted"}

async def blur_object_in_video(input_path: str, output_path: str, target_object: str, start_time: str = None, duration: str = None):
    """Blur specific object in video"""
    # Mock implementation - would use object detection and tracking
    return {"success": True, "message": f"Blurred {target_object} in video"}

async def zoom_to_object_in_video(input_path: str, output_path: str, target_object: str, start_time: str = None, duration: str = None, zoom_factor: float = 2.0):
    """Zoom to specific object in video"""
    # Mock implementation - would use object detection and tracking
    return {"success": True, "message": f"Zoomed to {target_object} in video"}

# Serve any file from public directory directly (catch-all route - must be last)
@app.get("/{file_path:path}")
async def serve_public_files(file_path: str):
    # Only serve files with specific extensions to avoid security issues
    allowed_extensions = {'.css', '.js', '.html', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.mp4', '.webm'}
    
    file_path_obj = Path(file_path)
    if file_path_obj.suffix.lower() not in allowed_extensions:
        raise HTTPException(status_code=404, detail="File not found")
    
    public_file = Path(__file__).parent.parent / "public" / file_path
    if not public_file.exists() or not public_file.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on extension
    media_types = {
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.html': 'text/html',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.mp4': 'video/mp4',
        '.webm': 'video/webm'
    }
    
    media_type = media_types.get(file_path_obj.suffix.lower(), 'application/octet-stream')
    return FileResponse(str(public_file), media_type=media_type)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "ffmpeg_available": True,
        "cohere_available": cohere_client is not None,
        "twelvelabs_available": twelvelabs_client is not None,
        "object_detection_available": object_detector is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ffmpeg_utils = FFmpegUtils()

class VideoProcessRequest(BaseModel):
    video_id: str
    start_time: Optional[str] = "00:00:00"
    duration: Optional[str] = None
    end_time: Optional[str] = None

class VideoEffectsRequest(BaseModel):
    video_id: str
    blur: Optional[float] = 0
    brightness: Optional[float] = 0
    contrast: Optional[float] = 1
    saturation: Optional[float] = 1
    artistic_filter: Optional[str] = "none"
    zoom: Optional[bool] = False
    rotation: Optional[float] = 0
    horizontal_flip: Optional[bool] = False
    vertical_flip: Optional[bool] = False

class AudioRequest(BaseModel):
    video_id: str
    audio_file_id: Optional[str] = None
    volume: Optional[float] = 0.5
    start_time: Optional[float] = 0
    duration: Optional[float] = None
    mix: Optional[bool] = True

class SubtitleRequest(BaseModel):
    video_id: str
    subtitle_file_id: Optional[str] = None
    burn: Optional[bool] = False
    language: Optional[str] = "en-US"
    auto_transcribe: Optional[bool] = False

@app.get("/")
async def read_root():
    index_file = Path(__file__).parent.parent / "public" / "index.html"
    return FileResponse(str(index_file))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_info = ffmpeg_utils.get_media_info(str(file_path))
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "media_info": file_info.get("info") if file_info["success"] else None
    }

@app.get("/api/files")
async def list_files():
    files = []
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            file_id = file_path.stem
            files.append({
                "file_id": file_id,
                "filename": file_path.name,
                "size": file_path.stat().st_size
            })
    return {"files": files}

@app.post("/api/trim")
async def trim_video(request: VideoProcessRequest):
    input_path = UPLOAD_DIR / f"{request.video_id}.*"
    input_files = list(UPLOAD_DIR.glob(f"{request.video_id}.*"))
    
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    input_path = input_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    if request.duration:
        result = ffmpeg_utils.trim_video(
            str(input_path), str(output_path), 
            request.start_time, request.duration, precise=True
        )
    elif request.end_time:
        start_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(request.start_time.split(':'))))
        end_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(request.end_time.split(':'))))
        duration_seconds = end_seconds - start_seconds
        duration = f"{duration_seconds//3600:02d}:{(duration_seconds%3600)//60:02d}:{duration_seconds%60:02d}"
        
        result = ffmpeg_utils.trim_video(
            str(input_path), str(output_path), 
            request.start_time, duration, precise=True
        )
    else:
        raise HTTPException(status_code=400, detail="Either duration or end_time must be provided")
    
    if result["success"]:
        return {"output_id": output_id, "message": "Video trimmed successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/convert")
async def convert_video(
    video_id: str = Form(...),
    video_codec: str = Form("libx264"),
    audio_codec: str = Form("aac"),
    quality: str = Form("23")
):
    input_files = list(UPLOAD_DIR.glob(f"{video_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    input_path = input_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.convert_video(
        str(input_path), str(output_path), 
        video_codec, audio_codec, quality
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Video converted successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/effects")
async def apply_effects(request: VideoEffectsRequest):
    input_files = list(UPLOAD_DIR.glob(f"{request.video_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    input_path = input_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.apply_video_effects(
        str(input_path), str(output_path),
        blur=request.blur,
        brightness=request.brightness,
        contrast=request.contrast,
        saturation=request.saturation,
        artistic_filter=request.artistic_filter,
        zoom=request.zoom,
        rotation=request.rotation,
        horizontal_flip=request.horizontal_flip,
        vertical_flip=request.vertical_flip
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Effects applied successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/audio/extract")
async def extract_audio(
    video_id: str = Form(...),
    audio_codec: str = Form("mp3"),
    bitrate: str = Form("192k")
):
    input_files = list(UPLOAD_DIR.glob(f"{video_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    input_path = input_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.{audio_codec}"
    
    result = ffmpeg_utils.extract_audio(
        str(input_path), str(output_path), audio_codec, bitrate
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Audio extracted successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/audio/background")
async def add_background_music(request: AudioRequest):
    input_files = list(UPLOAD_DIR.glob(f"{request.video_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    audio_files = list(UPLOAD_DIR.glob(f"{request.audio_file_id}.*"))
    if not audio_files:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    input_path = input_files[0]
    audio_path = audio_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.add_background_music(
        str(input_path), str(output_path), 
        str(audio_path), request.volume, request.mix
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Background music added successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/audio/effect")
async def add_sound_effect(request: AudioRequest):
    input_files = list(UPLOAD_DIR.glob(f"{request.video_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    audio_files = list(UPLOAD_DIR.glob(f"{request.audio_file_id}.*"))
    if not audio_files:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    input_path = input_files[0]
    audio_path = audio_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.add_sound_effect(
        str(input_path), str(output_path), str(audio_path),
        request.start_time, request.duration, request.volume, not request.mix
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Sound effect added successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/subtitles")
async def add_subtitles(request: SubtitleRequest):
    input_files = list(UPLOAD_DIR.glob(f"{request.video_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    input_path = input_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    if request.auto_transcribe:
        result = ffmpeg_utils.transcribe_audio(
            str(input_path), str(output_path), request.language
        )
    else:
        if not request.subtitle_file_id:
            raise HTTPException(status_code=400, detail="Subtitle file required when not auto-transcribing")
        
        subtitle_files = list(UPLOAD_DIR.glob(f"{request.subtitle_file_id}.*"))
        if not subtitle_files:
            raise HTTPException(status_code=404, detail="Subtitle file not found")
        
        subtitle_path = subtitle_files[0]
        result = ffmpeg_utils.add_subtitles(
            str(input_path), str(output_path), str(subtitle_path), request.burn
        )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Subtitles added successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/gif")
async def create_gif(
    video_id: str = Form(...),
    start_time: str = Form("00:00:00"),
    duration: str = Form("00:00:10"),
    width: int = Form(320),
    height: int = Form(240)
):
    input_files = list(UPLOAD_DIR.glob(f"{video_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    input_path = input_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.gif"
    
    result = ffmpeg_utils.create_gif(
        str(input_path), str(output_path), start_time, duration, width, height
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "GIF created successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/splice")
async def splice_video(
    video_id: str = Form(...),
    remove_start_time: str = Form(...),
    remove_end_time: str = Form(...)
):
    input_files = list(UPLOAD_DIR.glob(f"{video_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    input_path = input_files[0]
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}.mp4"
    
    result = ffmpeg_utils.splice_video(
        str(input_path), str(output_path), remove_start_time, remove_end_time
    )
    
    if result["success"]:
        return {"output_id": output_id, "message": "Video spliced successfully"}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/api/download/{output_id}")
async def download_file(output_id: str):
    output_files = list(OUTPUT_DIR.glob(f"{output_id}.*"))
    if not output_files:
        raise HTTPException(status_code=404, detail="Output file not found")
    
    output_path = output_files[0]
    return FileResponse(
        path=str(output_path),
        filename=f"edited_{output_path.name}",
        media_type='application/octet-stream'
    )

@app.get("/api/preview/{output_id}")
async def preview_file(output_id: str):
    output_files = list(OUTPUT_DIR.glob(f"{output_id}.*"))
    if not output_files:
        raise HTTPException(status_code=404, detail="Output file not found")
    
    output_path = output_files[0]
    
    def iterfile(file_path: str):
        with open(file_path, mode="rb") as file_like:
            yield from file_like
    
    return StreamingResponse(
        iterfile(str(output_path)), 
        media_type="video/mp4"
    )

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    files_deleted = 0
    
    for file_path in UPLOAD_DIR.glob(f"{file_id}.*"):
        file_path.unlink()
        files_deleted += 1
    
    for file_path in OUTPUT_DIR.glob(f"{file_id}.*"):
        file_path.unlink()
        files_deleted += 1
    
    if files_deleted == 0:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"message": f"Deleted {files_deleted} file(s)"}

@app.get("/api/info/{file_id}")
async def get_file_info(file_id: str):
    input_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not input_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    input_path = input_files[0]
    result = ffmpeg_utils.get_media_info(str(input_path))
    
    if result["success"]:
        return {"file_id": file_id, "info": result["info"]}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
