from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
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
import re
import speech_recognition as sr
from pydub import AudioSegment
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

# Import all backend modules
try:
    from .utils import FFmpegUtils
    from .object import ObjectTracker
    from . import output_utils
except ImportError:
    # Fallback when running as a script (no package context)
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

# Serve the main HTML file at root
@app.get("/")
async def serve_index():
    """Serve the main HTML file"""
    return FileResponse(str(public_dir / "index.html"))

# Serve other static files directly
@app.get("/{file_name}")
async def serve_static_file(file_name: str):
    """Serve static files like CSS, JS, images"""
    file_path = public_dir / file_name
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    raise HTTPException(status_code=404, detail="File not found")

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
    cohere_client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))

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

# -------------------------------
# Helper parsing utilities
# -------------------------------
def _normalize_quotes(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("\u2019", "'")
            .replace("\u2018", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
    )

def _extract_zoom_face_keyword(prompt: str) -> Optional[str]:
    """Extract keyword after phrases like 'talking about|says|mentions ...'.
    Robust to missing closing quotes and curly quotes. Returns None if not a
    zoom-face-with-topic request.
    """
    if not prompt:
        return None
    p_norm = _normalize_quotes(prompt)
    p_lower = p_norm.lower()
    # Must at least look like a face zoom request with a speaking topic
    if "zoom" not in p_lower or "face" not in p_lower:
        return None
    if not any(kw in p_lower for kw in [
        "talking about", "talks about", "saying", "says", "mentioning", "mentions"
    ]):
        return None

    # Regex with multiple groups for quoted/unquoted keywords (multi-word allowed)
    m = re.search(
        r"(?:talking about|talks about|saying|says|mentioning|mentions)\s+(?:\"([^\"]+)\"|'([^']+)'|([A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*))",
        p_norm,
        re.IGNORECASE,
    )
    if m:
        for g in m.groups():
            if g and g.strip():
                return g.strip().strip("'\".,!?:;()")

    # Fallback: take substring after the cue and strip leading quotes/punct
    cues = ["talking about", "talks about", "saying", "says", "mentioning", "mentions"]
    idx = -1
    cue_len = 0
    for cue in cues:
        pos = p_lower.find(cue)
        if pos != -1:
            idx = pos
            cue_len = len(cue)
            break
    if idx != -1:
        tail = p_norm[idx + cue_len :].strip()
        # Remove leading separators and quotes
        while tail and tail[0] in " \t'\"“”‘’:.-":
            tail = tail[1:]
        # Keyword ends at first punctuation if present
        end_pos = len(tail)
        for ch in [".", ",", ";", ":", "!", "?", "\n"]:
            cut = tail.find(ch)
            if cut != -1:
                end_pos = min(end_pos, cut)
        candidate = tail[:end_pos].strip().strip("'\"“”‘’")
        if candidate:
            # Limit to a few words to avoid capturing long phrases
            words = candidate.split()
            candidate = " ".join(words[:5])
            return candidate
    return None

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
        print(f"🎬 Processing AI edit request: {request.prompt} for file: {request.video_id}")
        
        if request.edit_type == "vague":
            # Process vague request
            result = await process_vague_request(request.prompt, str(input_path))
        else:
            # Process specific request
            result = await process_specific_request(request.prompt, str(input_path))
        
        print(f"✅ AI processing complete: {result}")
        return result
    except Exception as e:
        print(f"❌ AI processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

@app.post("/api/ai/edit/stream")
async def ai_powered_edit_stream(request: AIEditRequest):
    """AI-powered video editing with streaming progress updates"""
    if not cohere_client:
        raise HTTPException(status_code=503, detail="AI service not available - please set COHERE_API_KEY")
    
    async def generate_stream():
        try:
            yield f"data: {json.dumps({'status': 'started', 'message': 'Starting AI analysis...'})}\n\n"
            
            input_path = await get_input_file(request.video_id)
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Video file located, analyzing request...'})}\n\n"
            
            if request.edit_type == "vague":
                yield f"data: {json.dumps({'status': 'processing', 'message': 'Processing vague request with AI...'})}\n\n"
                result = await process_vague_request(request.prompt, str(input_path))
            else:
                yield f"data: {json.dumps({'status': 'processing', 'message': 'Processing specific request...'})}\n\n"
                result = await process_specific_request(request.prompt, str(input_path))
            
            yield f"data: {json.dumps({'status': 'completed', 'result': result})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': f'Error: {str(e)}'})}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")

@app.get("/api/ai/edit/stream/{video_id}")
async def ai_edit_stream_endpoint(video_id: str, prompt: str, edit_type: str = "specific"):
    """Stream endpoint for AI video editing with real-time updates"""
    if not cohere_client:
        return StreamingResponse(
            iter([f"data: {json.dumps({'status': 'error', 'message': 'AI service not available'})}\n\n"]),
            media_type="text/event-stream"
        )
    
    async def generate_stream():
        try:
            yield f"data: {json.dumps({'status': 'started', 'message': 'Initializing AI video editor...', 'progress': 10})}\n\n"
            await asyncio.sleep(0.5)
            
            # Validate file exists
            input_path = await get_input_file(video_id)
            yield f"data: {json.dumps({'status': 'processing', 'message': f'Video file found: {input_path.name}', 'progress': 20})}\n\n"
            await asyncio.sleep(0.5)
            
            # Analyze the prompt
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Analyzing your editing request...', 'progress': 30})}\n\n"
            await asyncio.sleep(1)
            
            # Process with AI
            if edit_type == "vague":
                yield f"data: {json.dumps({'status': 'processing', 'message': 'AI is generating editing commands...', 'progress': 50})}\n\n"
                result = await process_vague_request(prompt, str(input_path))
            else:
                yield f"data: {json.dumps({'status': 'processing', 'message': 'Processing specific editing commands...', 'progress': 50})}\n\n"
                result = await process_specific_request(prompt, str(input_path))
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'AI analysis complete, preparing response...', 'progress': 80})}\n\n"
            await asyncio.sleep(0.5)
            
            # Use the output filename that was actually created by the processing function
            # Don't overwrite it with a new timestamp
            if not result.get('output_file'):
                # Fallback only if no output_file was set
                timestamp = int(time.time())
                output_filename = f"ai_edited_{video_id[:8]}_{timestamp}.mp4"
                result['output_file'] = output_filename
                result['output_path'] = f"outputs/{output_filename}"
            
            yield f"data: {json.dumps({'status': 'completed', 'message': 'Video editing analysis complete!', 'progress': 100, 'result': result})}\n\n"
            
        except Exception as e:
            print(f"❌ Streaming error: {str(e)}")
            yield f"data: {json.dumps({'status': 'error', 'message': f'Error: {str(e)}', 'progress': 0})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

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
        message=analysis_prompt
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
    
    # For demo purposes, use a default index - in production, track your uploaded video/index IDs
    try:
        # Debug: list indexes and pick the most recent one
        print("🔎 Listing TwelveLabs indexes...")
        indexes = twelvelabs_client.indexes.list(page=1, page_limit=5, sort_by="created_at", sort_option="desc")
        print(f"📦 Indexes response: {indexes}")
        if not indexes.data:
            raise HTTPException(status_code=404, detail="No TwelveLabs indexes found. Upload first.")
        index_id = indexes.data[0].id
        print(f"✅ Using index: {index_id}")

        # Debug: list videos for the index
        videos = twelvelabs_client.indexes.videos.list(index_id=index_id, page=1, page_limit=10, sort_by="created_at", sort_option="desc")
        print(f"🎞️ Videos response: {videos}")
        if not videos.data:
            raise HTTPException(status_code=404, detail="No videos in TwelveLabs index. Upload first.")
        video_id = videos.data[0].id
        print(f"🎯 Searching in video: {video_id}")

        # Perform a text search
        print(f"🔍 Running TL search for query: {request.query}")
        result = twelvelabs_client.search.query(index_id=index_id, query_text=request.query, page=1, page_limit=5)
        print(f"🧾 Raw TL search result: {result}")

        # Build a simple response with segment start/end if available
        segments = []
        try:
            for item in getattr(result, 'data', []) or []:
                start = getattr(item, 'start', None)
                end = getattr(item, 'end', None)
                score = getattr(item, 'score', None)
                if start is not None and end is not None:
                    segments.append({"start": float(start), "end": float(end), "score": float(score) if score is not None else None})
        except Exception as parse_err:
            print(f"⚠️ Could not parse TL segments: {parse_err}")

        return {
            "query": request.query,
            "index_id": index_id,
            "video_id": video_id,
            "segments": segments,
            "raw": str(result)
        }
    except Exception as e:
        print(f"❌ TwelveLabs search error: {e}")
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

class ExportRequest(BaseModel):
    videoId: str
    format: str = "mp4"
    quality: str = "high"

@app.post("/api/export")
async def export_video(request: ExportRequest):
    """Export video with specified format and quality"""
    try:
        # Get input file
        input_files = list(UPLOAD_DIR.glob(f"{request.videoId}.*"))
        if not input_files:
            raise HTTPException(status_code=404, detail="Video not found")
        
        input_path = input_files[0]
        output_id = str(uuid.uuid4())
        output_path = OUTPUT_DIR / f"{output_id}.{request.format}"
        
        # Quality settings
        quality_settings = {
            "high": {"scale": "1920:1080", "bitrate": "5M"},
            "medium": {"scale": "1280:720", "bitrate": "3M"},
            "low": {"scale": "854:480", "bitrate": "1M"},
            "original": {"scale": None, "bitrate": None}
        }
        
        settings = quality_settings.get(request.quality, quality_settings["high"])
        
        # Use convert function for format conversion
        result = ffmpeg_utils.convert_video(
            str(input_path), 
            str(output_path), 
            request.format,
            scale=settings["scale"],
            bitrate=settings["bitrate"]
        )
        
        if result["success"]:
            # Return the file directly as download
            return FileResponse(
                path=str(output_path),
                filename=f"exported_{input_path.stem}.{request.format}",
                media_type='application/octet-stream'
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/preview/{file_id}")
async def preview_file(file_id: str, request: Request):
    """Stream video preview with Range support for seeking"""
    # Try output files first, then uploaded files
    file_paths = list(OUTPUT_DIR.glob(f"{file_id}.*")) + list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not file_paths:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = file_paths[0]
    media_type = "video/mp4" if file_path.suffix.lower() in ['.mp4', '.mov', '.avi'] else "application/octet-stream"

    # Implement HTTP Range support
    range_header = request.headers.get('range') or request.headers.get('Range')
    file_size = file_path.stat().st_size
    headers = {"Accept-Ranges": "bytes"}
    if range_header:
        # bytes=start-end
        import re
        m = re.match(r"bytes=(\d+)-(\d+)?", range_header)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else file_size - 1
            start = max(0, start)
            end = min(file_size - 1, end)
            if start > end:
                start, end = 0, file_size - 1
            length = end - start + 1
            def iter_range():
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = length
                    chunk = 1024 * 1024
                    while remaining > 0:
                        data = f.read(min(chunk, remaining))
                        if not data:
                            break
                        remaining -= len(data)
                        yield data
            headers.update({
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(length)
            })
            return StreamingResponse(iter_range(), status_code=206, media_type=media_type, headers=headers)
    def iter_full():
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(1024 * 1024)
                if not data:
                    break
                yield data
    headers["Content-Length"] = str(file_size)
    return StreamingResponse(iter_full(), media_type=media_type, headers=headers)

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

@app.get("/api/outputs/{filename}")
async def download_output(filename: str, request: Request):
    """Download or stream a processed output file with Range support"""
    output_path = OUTPUT_DIR / filename
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    media_type = "video/mp4" if output_path.suffix.lower() in ['.mp4', '.mov', '.avi'] else "application/octet-stream"
    # Reuse same Range logic as preview
    range_header = request.headers.get('range') or request.headers.get('Range')
    file_size = output_path.stat().st_size
    headers = {"Accept-Ranges": "bytes", "Content-Disposition": f"inline; filename={filename}", "Cache-Control": "no-cache"}
    if range_header:
        import re
        m = re.match(r"bytes=(\d+)-(\d+)?", range_header)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else file_size - 1
            start = max(0, start)
            end = min(file_size - 1, end)
            if start > end:
                start, end = 0, file_size - 1
            length = end - start + 1
            def iter_range():
                with open(output_path, 'rb') as f:
                    f.seek(start)
                    remaining = length
                    chunk = 1024 * 1024
                    while remaining > 0:
                        data = f.read(min(chunk, remaining))
                        if not data:
                            break
                        remaining -= len(data)
                        yield data
            headers.update({
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(length)
            })
            return StreamingResponse(iter_range(), status_code=206, media_type=media_type, headers=headers)
    def iter_full():
        with open(output_path, 'rb') as f:
            while True:
                data = f.read(1024 * 1024)
                if not data:
                    break
                yield data
    headers["Content-Length"] = str(file_size)
    return StreamingResponse(iter_full(), media_type=media_type, headers=headers)

# ====================
# UTILITY FUNCTIONS
# ====================

async def get_input_file(file_id: str) -> Path:
    """Get input file path from uploads or outputs and validate existence"""
    # Try uploads first
    input_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if input_files:
        return input_files[0]
    # Then outputs (so we can chain edits on processed video)
    output_files = list(OUTPUT_DIR.glob(f"{file_id}.*"))
    if output_files:
        return output_files[0]
    raise HTTPException(status_code=404, detail="File not found")

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

# ---------- Internal helpers for AI edit processing ----------
def _get_video_duration_seconds(path: str) -> Optional[float]:
    """Return duration in seconds if available via ffprobe output."""
    try:
        result = ffmpeg_utils.get_media_info(str(path))
        if not result.get("success"):
            return None
        info = result.get("info", {})
        # Prefer format.duration
        fmt = info.get("format") if isinstance(info, dict) else None
        if isinstance(fmt, dict) and "duration" in fmt:
            try:
                return float(fmt["duration"])
            except Exception:
                pass
        # Fallback: any stream.duration
        for s in info.get("streams", []) if isinstance(info, dict) else []:
            if isinstance(s, dict) and "duration" in s:
                try:
                    return float(s["duration"])
                except Exception:
                    continue
    except Exception:
        return None
    return None

def _parse_time_token(token: str) -> Optional[float]:
    """Parse a time token like '01:23:45', '1:23', '90s', '2m', '1.5h' into seconds."""
    t = (token or '').strip().lower()
    # HH:MM:SS(.ms) or MM:SS(.ms)
    if re.match(r'^\d{1,2}:\d{2}(:\d{2}(?:\.\d+)?)?$', t):
        parts = t.split(':')
        try:
            if len(parts) == 3:
                hours = int(parts[0]); minutes = int(parts[1]); seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            if len(parts) == 2:
                minutes = int(parts[0]); seconds = float(parts[1])
                return minutes * 60 + seconds
        except Exception:
            return None
    m = re.match(r'^(\d+(?:\.\d+)?)(\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds))?$', t)
    if m:
        value = float(m.group(1))
        unit = (m.group(3) or 's').lower()
        if unit.startswith('h'):
            return value * 3600
        if unit.startswith('m'):
            return value * 60
        return value
    return None

def _parse_location_range(text: str, duration: Optional[float]) -> Optional[tuple[float, float]]:
    """Parse a free-text location description into a (start,end) in seconds."""
    if not text:
        return None
    t = text.strip().lower()
    # first/last/middle patterns
    m = re.search(r'first\s+(\d+(?:\.\d+)?)\s*seconds?', t)
    if m:
        secs = float(m.group(1))
        return (0.0, max(0.0, secs))
    m = re.search(r'last\s+(\d+(?:\.\d+)?)\s*seconds?', t)
    if m and duration is not None:
        secs = float(m.group(1))
        start = max(0.0, float(duration) - secs)
        return (start, float(duration))
    m = re.search(r'middle\s+(\d+(?:\.\d+)?)\s*seconds?', t)
    if m and duration is not None:
        secs = float(m.group(1))
        start = max(0.0, float(duration) / 2.0 - secs / 2.0)
        end = min(float(duration), start + secs)
        return (start, end)
    # at X for Y seconds
    m = re.search(r'(?:at|from)\s+([^\s,]+)\s+(?:for)\s+(\d+(?:\.\d+)?)\s*seconds?', t)
    if m:
        start_sec = _parse_time_token(m.group(1))
        dur_sec = float(m.group(2))
        if start_sec is not None:
            return (max(0.0, start_sec), max(0.0, start_sec + dur_sec))
    # generic range: X to Y or X - Y
    m = re.search(r'([^\s,]+)\s*(?:to|-)\s*([^\s,]+)', t)
    if m:
        s1 = _parse_time_token(m.group(1))
        s2 = _parse_time_token(m.group(2))
        if s1 is not None and s2 is not None and s2 > s1:
            return (max(0.0, s1), s2)
        # Interpret "to Y" with missing or zero start as 0→Y
        if (m.group(1) in {"to", "0", "00:00", "00:00:00"} or s1 == 0) and s2 is not None and s2 > 0:
            return (0.0, s2)
    # handle phrasing like "trim to 5 seconds" => 0→5s
    m = re.search(r'(?:to|upto|up to)\s+(\d+(?:\.\d+)?)\s*seconds?', t)
    if m:
        secs = float(m.group(1))
        if secs > 0:
            return (0.0, secs)
    # any two time-like tokens
    tokens = re.findall(r'(\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?|\d+(?:\.\d+)?\s*(?:h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds))', t)
    if len(tokens) >= 2:
        s1 = _parse_time_token(tokens[0])
        s2 = _parse_time_token(tokens[1])
        if s1 is not None and s2 is not None and s2 > s1:
            return (max(0.0, s1), s2)
    # single time token like "5s" can be interpreted as 0→5s
    if len(tokens) == 1:
        s = _parse_time_token(tokens[0])
        if s is not None and s > 0:
            return (0.0, s)
    return None

def _parse_front_back_cuts(text: str) -> tuple[float, float]:
    """Return (front_cut_seconds, back_cut_seconds) parsed from text.
    Interprets phrases like 'first 10 seconds', 'last 2 seconds',
    'minus 10 from the front', 'minus 2 from the back'.
    """
    t = (text or '').lower()
    front_cut = 0.0
    back_cut = 0.0
    # first X seconds => remove first X
    m = re.findall(r'first\s+(\d+(?:\.\d+)?)\s*seconds?', t)
    for val in m:
        front_cut = max(front_cut, float(val))
    # last X seconds => remove last X
    m = re.findall(r'last\s+(\d+(?:\.\d+)?)\s*seconds?', t)
    for val in m:
        back_cut = max(back_cut, float(val))
    # minus X from the front/start
    m = re.findall(r'minus\s+(\d+(?:\.\d+)?)\s*(?:seconds?|s)?\s+from\s+the\s+(?:front|start)', t)
    for val in m:
        front_cut = max(front_cut, float(val))
    # minus X from the back/end
    m = re.findall(r'minus\s+(\d+(?:\.\d+)?)\s*(?:seconds?|s)?\s+from\s+the\s+(?:back|end)', t)
    for val in m:
        back_cut = max(back_cut, float(val))
    return front_cut, back_cut

def infer_trim_range_from_prompt_and_instances(prompt: str, instances: list[list[str]], duration: Optional[float]) -> Optional[tuple[float, float]]:
    """Infer a single (start,end) keep-range from the user's prompt and AI instances.
    Combines explicit ranges with front/back cuts logically.
    """
    # Aggregate ranges and cuts from both prompt and instance locations
    allowed_start: Optional[float] = 0.0 if duration is not None else None
    allowed_end: Optional[float] = float(duration) if duration is not None else None
    collected_ranges: list[tuple[float, float]] = []
    front_cut_total = 0.0
    back_cut_total = 0.0

    # From entire prompt
    f_cut, b_cut = _parse_front_back_cuts(prompt)
    front_cut_total = max(front_cut_total, f_cut)
    back_cut_total = max(back_cut_total, b_cut)
    rng = _parse_location_range(prompt, duration)
    if rng is not None and not re.search(r'\b(first|last)\b', (prompt or '').lower()):
        collected_ranges.append(rng)

    # From each instance location
    for _, location in instances:
        f_cut, b_cut = _parse_front_back_cuts(location)
        front_cut_total = max(front_cut_total, f_cut)
        back_cut_total = max(back_cut_total, b_cut)
        rng = _parse_location_range(location, duration)
        # Avoid treating 'first X seconds' as a keep range; already captured as cut
        if rng is not None and not re.search(r'\b(first|last)\b', location.lower()):
            collected_ranges.append(rng)

    # Narrow allowed range by intersections
    for r_start, r_end in collected_ranges:
        if allowed_start is None and allowed_end is None:
            allowed_start, allowed_end = r_start, r_end
        else:
            # Use existing bounds (if None, infer from duration if available)
            cur_start = allowed_start if allowed_start is not None else 0.0
            cur_end = allowed_end if allowed_end is not None else (float(duration) if duration is not None else r_end)
            # Intersect
            new_start = max(cur_start, r_start)
            new_end = min(cur_end, r_end)
            allowed_start, allowed_end = new_start, new_end

    # If we have only cuts but no explicit duration, we still need duration to compute back cuts
    if allowed_start is None and allowed_end is None and duration is not None:
        allowed_start, allowed_end = 0.0, float(duration)

    if allowed_start is None or allowed_end is None:
        return None

    # Apply front/back cuts to the allowed range
    start = allowed_start + front_cut_total
    end = allowed_end - back_cut_total
    if duration is not None:
        start = max(0.0, min(start, float(duration)))
        end = max(0.0, min(end, float(duration)))

    if end - start <= 0:
        return None
    return (start, end)

def _parse_speed_factor(text: str) -> Optional[float]:
    """Parse speed change factor from text. Examples:
    - "speed up by 2x" => 2.0
    - "speed up 2x" => 2.0
    - "2x speed" / "2x faster" => 2.0
    - "slow down to 0.5x" => 0.5
    - "slow down by 2x" => 0.5 (interpret as twice slower)
    - "half speed" => 0.5
    - "double speed" => 2.0
    """
    if not text:
        return None
    t = text.lower()
    # Words
    if "double speed" in t or "twice as fast" in t:
        return 2.0
    if "half speed" in t or "half as fast" in t:
        return 0.5
    # patterns like 0.5x, 2x
    m = re.search(r"(\d+(?:\.\d+)?)\s*x", t)
    if m:
        x = float(m.group(1))
        if "slow" in t:
            # "slow down by 2x" means half speed
            # "slow down to 0.5x" handled naturally below
            if re.search(r"slow[^.]*\bto\b", t):
                return x
            return 1.0 / x if x != 0 else None
        return x
    # phrases: speed up/slow down by/to N
    m = re.search(r"speed up (?:by|to)?\s*(\d+(?:\.\d+)?)", t)
    if m:
        return float(m.group(1))
    m = re.search(r"slow down (?:to)\s*(\d+(?:\.\d+)?)", t)
    if m:
        return float(m.group(1))
    m = re.search(r"slow down (?:by)\s*(\d+(?:\.\d+)?)", t)
    if m:
        x = float(m.group(1))
        return 1.0 / x if x != 0 else None
    return None

def _find_keyword_segments_in_audio(video_path: str, keyword: str, language: str = "en-US") -> List[tuple[float, float]]:
    """Rough speech-based search: returns list of (start,end) seconds where keyword occurs.
    Approach: extract mono wav, window into chunks (e.g., 2.5s with 1.25s hop),
    use speech_recognition Google recognizer for lightweight keyword presence.
    """
    try:
        # Extract audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        ffprobe = ffmpeg_utils.get_media_info(video_path)
        if not ffprobe.get("success"):
            return []
        # Use our extractor from utils
        extract_cmd = [ffmpeg_utils.ffmpeg_path, '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', '-y', temp_audio_path]
        _ = ffmpeg_utils._run_command(extract_cmd, "Audio Extraction for Keyword Search")
        if not os.path.exists(temp_audio_path):
            return []
        # Load audio and scan
        audio = AudioSegment.from_wav(temp_audio_path)
        total_ms = len(audio)
        recognizer = sr.Recognizer()
        window_ms = 2500
        hop_ms = 1250
        hits: List[tuple[float, float]] = []
        k = keyword.strip().lower()
        for start_ms in range(0, total_ms, hop_ms):
            seg = audio[start_ms:start_ms + window_ms]
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as seg_file:
                seg.export(seg_file.name, format="wav")
                seg_path = seg_file.name
            try:
                with sr.AudioFile(seg_path) as source:
                    audio_data = recognizer.record(source)
                    try:
                        text = recognizer.recognize_google(audio_data, language=language)
                    except sr.UnknownValueError:
                        text = ""
                if k and k in text.lower():
                    # Mark the whole window as a hit; we can refine later if needed
                    s = start_ms / 1000.0
                    e = min((start_ms + window_ms) / 1000.0, total_ms / 1000.0)
                    hits.append((s, e))
            finally:
                if os.path.exists(seg_path):
                    os.remove(seg_path)
        # Merge overlapping hits
        if not hits:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            return []
        hits.sort()
        merged: List[tuple[float, float]] = []
        cur_s, cur_e = hits[0]
        for s, e in hits[1:]:
            if s <= cur_e + 0.25:
                cur_e = max(cur_e, e)
            else:
                merged.append((cur_s, cur_e))
                cur_s, cur_e = s, e
        merged.append((cur_s, cur_e))
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        return merged
    except Exception:
        return []

async def process_vague_request(prompt: str, video_path: str) -> Dict[str, Any]:
    """Process vague editing request using AI and execute the editing"""
    print(f"🎬 Processing vague request: {prompt}")
    
    # First, get AI analysis
    analysis_prompt = f"""
    You are given a vague video edit request. Generate specific editing commands based on this request.
    Request: "{prompt}"
    
    Available edit techniques: speed up video, slow down video, clip trimming, transitions, 
    audio effects, dynamic zoom, object face blur, face/object tracking, subtitles, video effects.
    
    Return editing commands in this format:
    <command> AND <where in video it should be applied>
    """
    
    response = cohere_client.chat(
        model="command-r-plus",
        message=analysis_prompt
    )
    
    commands = extract_response_text(response)
    print(f"🤖 AI Commands: {commands}")
    
    # Generate proper output filename with ai_edited prefix
    timestamp = int(time.time())
    
    # Extract video_id from video_path if possible
    video_path_obj = Path(video_path)
    video_id = video_path_obj.stem  # Get filename without extension
    
    # Create output filename with proper format
    output_filename = f"ai_edited_{video_id[:8]}_{timestamp}.mp4"
    output_path = OUTPUT_DIR / output_filename
    
    print(f"📝 Creating output file: {output_filename}")
    
    # Set input path
    input_path = Path(video_path)
    
    try:
        # Parse the user's intent and apply appropriate effects
        prompt_lower = prompt.lower()
        print(f"🔍 Parsing prompt: '{prompt_lower}'")
        print(f"🔍 Contains 'blur': {'blur' in prompt_lower}")
        print(f"🔍 Contains 'face': {'face' in prompt_lower}")
        
        speed_factor = _parse_speed_factor(prompt)
        if speed_factor is None and ("speed up" in prompt_lower or "slower" in prompt_lower or "slow down" in prompt_lower or re.search(r"\b\d+(?:\.\d+)?x\b", prompt_lower)):
            # Default factors when phrase exists but no number given
            speed_factor = 2.0 if "speed up" in prompt_lower else 0.5
        if speed_factor is not None:
            if speed_factor > 1.0:
                print(f"🚀 Applying speed up effect {speed_factor}x...")
            else:
                print(f"🐌 Applying slow down effect to {speed_factor}x...")
            result = ffmpeg_utils.apply_video_effects(
                str(input_path), 
                str(output_path),
                effects={
                    "speed": float(speed_factor),
                    "audio_tempo": float(speed_factor)
                }
            )
        elif "blur" in prompt_lower:
            print(f"🔍 Blur detected in prompt: '{prompt_lower}'")
            # ALWAYS use ObjectProcessor for face blur - assume blur means face blur
            print("👤 Face blur requested - using ObjectProcessor...")
            print(f"📁 Input path: {input_path}")
            print(f"📁 Output path: {output_path}")
            
            # Use ObjectProcessor for face blur
            face_blur_result = await blur_object_in_video(
                str(input_path),
                str(output_path), 
                "face"
            )
            
            print(f"🎭 Face blur result: {face_blur_result}")
            
            # Convert blur result to expected format
            if face_blur_result and face_blur_result.get("success"):
                result = {"success": True, "message": "Face blur applied successfully"}
            else:
                result = {"success": False, "error": face_blur_result.get("message", "Face blur failed")}
        elif "bright" in prompt_lower:
            print("☀️ Applying brightness effect...")
            result = ffmpeg_utils.apply_video_effects(
                str(input_path), 
                str(output_path),
                effects={"brightness": 0.3}
            )
        elif "trim" in prompt_lower or "cut" in prompt_lower or "remove" in prompt_lower:
            print("✂️ Applying trim/cut effect...")
            
            # Parse trim instructions from the prompt
            import re
            
            # Check for "last X seconds" pattern
            last_seconds_match = re.search(r'last (\d+(?:\.\d+)?)\s*seconds?', prompt_lower)
            first_seconds_match = re.search(r'first (\d+(?:\.\d+)?)\s*seconds?', prompt_lower)
            
            if last_seconds_match:
                # Trim the last X seconds - need to get video duration first
                seconds_to_trim = float(last_seconds_match.group(1))
                print(f"🔍 Trimming last {seconds_to_trim} seconds")
                
                # Get video duration to calculate duration to keep
                video_duration = _get_video_duration_seconds(str(input_path))
                if video_duration is not None:
                    duration_to_keep = video_duration - seconds_to_trim
                    
                    # Convert to HH:MM:SS format
                    duration_str = f"{int(duration_to_keep//3600):02d}:{int((duration_to_keep%3600)//60):02d}:{duration_to_keep%60:06.3f}"
                    start_time_str = "00:00:00"
                    
                    print(f"📏 Video duration: {video_duration}s, keeping {duration_to_keep}s (duration: {duration_str})")
                    
                    # Apply trim using FFmpeg
                    result = ffmpeg_utils.trim_video(
                        str(input_path),
                        str(output_path),
                        start_time_str,
                        duration_str,
                        precise=True
                    )
                    print(f"✂️ Trim result: {result}")
                else:
                    print("❌ Could not get video duration for trimming")
                    result = {"success": False, "error": "Could not determine video duration"}
                    
            elif first_seconds_match:
                # Trim the first X seconds (keep everything after X seconds)
                seconds_to_trim = float(first_seconds_match.group(1))
                print(f"🔍 Trimming first {seconds_to_trim} seconds")
                
                # Get video duration to calculate remaining duration
                video_duration = _get_video_duration_seconds(str(input_path))
                if video_duration is not None:
                    duration_to_keep = video_duration - seconds_to_trim
                    
                    # Convert to HH:MM:SS format
                    start_time_str = f"{int(seconds_to_trim//3600):02d}:{int((seconds_to_trim%3600)//60):02d}:{seconds_to_trim%60:06.3f}"
                    duration_str = f"{int(duration_to_keep//3600):02d}:{int((duration_to_keep%3600)//60):02d}:{duration_to_keep%60:06.3f}"
                    
                    print(f"📏 Video duration: {video_duration}s, starting at {seconds_to_trim}s, keeping {duration_to_keep}s")
                    
                    # Apply trim using FFmpeg
                    result = ffmpeg_utils.trim_video(
                        str(input_path),
                        str(output_path),
                        start_time_str,
                        duration_str,
                        precise=True
                    )
                    print(f"✂️ Trim result: {result}")
                else:
                    print("❌ Could not get video duration for trimming")
                    result = {"success": False, "error": "Could not determine video duration"}
            else:
                print("❌ Could not parse trim instructions from prompt")
                result = {"success": False, "error": "Could not parse trim instructions - try 'trim the last 5 seconds' or 'trim the first 3 seconds'"}
                
        elif "zoom" in prompt_lower:
            # Check if it's face/person zoom
            if "face" in prompt_lower or "person" in prompt_lower or "people" in prompt_lower:
                print("🔍 Face zoom requested - using ObjectProcessor...")
                result = await zoom_to_object_in_video(
                    str(input_path),
                    str(output_path), 
                    "face",
                    zoom_factor=2.0
                )
            else:
                print("🔍 General zoom requested...")
                # Apply general zoom effect
                result = ffmpeg_utils.apply_video_effects(
                    str(input_path), 
                    str(output_path),
                    effects={"zoom": 1.5}
                )
        else:
            # Default: apply a subtle enhancement
            print("✨ Applying default enhancement...")
            result = ffmpeg_utils.apply_video_effects(
                str(input_path), 
                str(output_path),
                effects={
                    "contrast": 1.1,
                    "saturation": 1.05
                }
            )
        
        if result and result.get("success"):
            print(f"✅ Video processing successful: {output_path}")
            return {
                "type": "vague", 
                "commands": commands, 
                "status": "completed",
                "output_file": output_filename,
                "output_path": str(output_path),
                "success": True
            }
        else:
            print(f"❌ Video processing failed: {result}")
            return {
                "type": "vague", 
                "commands": commands, 
                "status": "error",
                "error": result.get("error", "Unknown processing error") if result else "Processing failed"
            }
            
    except Exception as e:
        print(f"❌ Exception during video processing: {str(e)}")
        return {
            "type": "vague", 
            "commands": commands, 
            "status": "error",
            "error": f"Processing exception: {str(e)}"
        }

async def process_specific_request(prompt: str, video_path: str) -> Dict[str, Any]:
    """Process specific editing request using the logic from specific.py"""
    try:
        print(f"🎯 Processing specific request: {prompt}")
        prompt_lower = (prompt or '').lower()

        # Fast-path: handle "keep only the part where (he|she|they) says <keyword>" without relying on AI parsing
        if re.search(r"\bkeep( only)? (the )?part where (he|she|they) says\b", prompt_lower):
            print("🛣️ Fast-path: keyword-based keep detected from prompt")
            # Try to extract keyword after 'says'
            kw_match = re.search(r"\bsays\s+([a-zA-Z0-9\-]+)\b", prompt, re.IGNORECASE)
            if not kw_match:
                # Try quoted keyword: says "..."
                q = re.search(r"\bsays\s+['\"]([^'\"]+)['\"]", prompt, re.IGNORECASE)
                if q:
                    keyword = q.group(1).strip()
                else:
                    keyword = None
            else:
                keyword = kw_match.group(1).strip()
            if not keyword:
                return {
                    "type": "specific",
                    "commands": prompt,
                    "status": "error",
                    "error": "Could not extract keyword after 'says'"
                }
            print(f"🔑 Keyword extracted: {keyword}")
            segments = _find_keyword_segments_in_audio(video_path, keyword)
            if not segments:
                return {
                    "type": "specific",
                    "commands": prompt,
                    "status": "error",
                    "error": f"Could not find any segment where '{keyword}' is spoken"
                }
            # Choose the longest segment and add small padding
            seg = max(segments, key=lambda r: r[1] - r[0])
            pad = 0.25
            s = max(0.0, seg[0] - pad)
            e = seg[1] + pad
            print(f"⏱️ Keeping keyword segment: {s:.3f}s → {e:.3f}s")

            # Build output filename
            timestamp = int(time.time())
            video_path_obj = Path(video_path)
            video_id = video_path_obj.stem
            output_filename = f"ai_edited_{video_id[:8]}_{timestamp}.mp4"
            output_path = OUTPUT_DIR / output_filename

            start_time = f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{s%60:06.3f}"
            duration_time = f"{int((e-s)//3600):02d}:{int(((e-s)%3600)//60):02d}:{(e-s)%60:06.3f}"
            print(f"✂️ Trimming from {start_time} for duration {duration_time}")
            result = ffmpeg_utils.trim_video(
                str(video_path),
                str(output_path),
                start_time,
                duration_time,
                precise=True
            )
            if result.get("success"):
                return {
                    "type": "specific",
                    "commands": f"Keep AND says {keyword}",
                    "status": "completed",
                    "output_file": output_filename,
                    "output_path": str(output_path),
                    "success": True
                }
            return {
                "type": "specific",
                "commands": prompt,
                "status": "error",
                "error": f"Trim failed: {result.get('error', 'unknown error')}"
            }

        # Fast-path: zoom into the person's face when he is talking about <keyword>
        keyword = _extract_zoom_face_keyword(prompt)
        if keyword:
            keyword = keyword.strip()
            if not keyword:
                return {
                    "type": "specific",
                    "commands": prompt,
                    "status": "error",
                    "error": "Could not extract topic keyword"
                }

            print(f"🔎 Face zoom keyword parsed: '{keyword}'")
            # Find audio segments containing the keyword
            segments = _find_keyword_segments_in_audio(video_path, keyword)
            print(f"🧩 Keyword segments found: {segments}")
            if not segments:
                return {
                    "type": "specific",
                    "commands": prompt,
                    "status": "error",
                    "error": f"Could not find any segment where '{keyword}' is spoken"
                }

            # Build output filename
            timestamp = int(time.time())
            video_path_obj = Path(video_path)
            video_id = video_path_obj.stem
            output_filename = f"ai_edited_{video_id[:8]}_{timestamp}.mp4"
            output_path = OUTPUT_DIR / output_filename

            # Apply face-zoom only during those segments by using ObjectProcessor with time-gated zoom
            try:
                try:
                    from .object import ObjectProcessor
                except ImportError:
                    from object import ObjectProcessor
                # Log where ObjectProcessor is coming from
                try:
                    import inspect
                    print(f"🧩 Using ObjectProcessor from: {inspect.getsourcefile(ObjectProcessor)}")
                except Exception:
                    pass

                processor = ObjectProcessor(
                    input_video_path=str(video_path),
                    detection_type="faces",
                    verbose=True
                )
                # Slight padding around speaking windows
                padded = [(max(0.0, s - 0.2), e + 0.2) for s, e in segments]
                processor.enable_object_zoom(zoom_factor=3.5)
                # Turn on on-frame debug overlay to verify boxes/zoom state
                if hasattr(processor, 'enable_debug_overlay'):
                    processor.enable_debug_overlay(False)
                # Log which face backend we use
                try:
                    print(f"🧠 Face backend: {getattr(processor, 'face_backend', 'unknown')}")
                except Exception:
                    pass
                if hasattr(processor, 'set_zoom_time_segments'):
                    processor.set_zoom_time_segments(padded)
                success = processor.process_and_save(str(output_path))
                if success and output_path.exists():
                    print(f"✅ Face zoom with time-gated segments complete. Output: {output_path}")
                    return {
                        "type": "specific",
                        "commands": f"Zoom face AND when saying {keyword}",
                        "status": "completed",
                        "output_file": output_filename,
                        "output_path": str(output_path),
                        "success": True
                    }
                return {
                    "type": "specific",
                    "commands": prompt,
                    "status": "error",
                    "error": "Face zoom processing failed"
                }
            except Exception as e:
                return {
                    "type": "specific",
                    "commands": prompt,
                    "status": "error",
                    "error": f"Exception during face zoom: {str(e)}"
                }
        
        # Step 1: Extract commands from prompt (similar to intent_extraction in specific.py)
        extraction_prompt = f"""
        Extract the specific video edit commands from the following user request. 
        Output them **only** in this exact format: 
        <command> AND <where in the video/audio it should be applied>, 
        <command> AND <where in the video/audio it should be applied>, 
        … (continue as needed). 
        Do not include section titles, explanations, or any extra text—just the commands in the specified format. 
        Here is the user request: '{prompt}'. 
        Available edit techniques: clip trimming, transitions, audio effects, dynamic zoom, face zoom, object face blur, 
        face/object tracking, subtitles, add subtitles, video effects, apply video effects, blur, saturation, 
        brightness, contrast, artistic filters, sound effects (boom, gunshot, explosion, whoosh), splice.
        """
        
        response = cohere_client.chat(
            model="command-r-plus",
            message=extraction_prompt
        )
        
        commands_text = extract_response_text(response)
        print(f"🤖 AI Commands: {commands_text}")
        
        # Parse commands into list format
        edits = commands_text.split(",")
        instances = []
        for edit in edits:
            parts = edit.strip().split(" AND ")
            if len(parts) == 2:
                command = parts[0].strip().replace("<", "").replace(">", "")
                location = parts[1].strip().replace("<", "").replace(">", "")
                instances.append([command, location])
        
        print(f"📝 Parsed instances: {instances}")
        
        # Direct zoom handling to ensure we use ObjectProcessor (faces/objects)
        zoom_cmd_idx = None
        zoom_location = ""
        for idx, (cmd, loc) in enumerate(instances):
            if any(t in cmd.lower() for t in ["zoom", "dynamic zoom", "zoom effect", "zoom into", "zoom on"]):
                zoom_cmd_idx = idx
                zoom_location = loc or ""
                break
        if zoom_cmd_idx is not None or "zoom" in prompt_lower:
            try:
                try:
                    from .object import ObjectProcessor
                except ImportError:
                    from object import ObjectProcessor
                # Log source of ObjectProcessor
                try:
                    import inspect
                    print(f"🧩 Using ObjectProcessor from: {inspect.getsourcefile(ObjectProcessor)}")
                except Exception:
                    pass

                # Determine detection mode
                text_for_target = f"{zoom_location} {prompt_lower}"
                is_face = any(k in text_for_target for k in ["face", "person", "people"]) 
                detection_type = "faces" if is_face else "objects"

                # Output filename
                timestamp = int(time.time())
                video_path_obj = Path(video_path)
                video_id = video_path_obj.stem
                output_filename = f"ai_edited_{video_id[:8]}_{timestamp}.mp4"
                output_path = OUTPUT_DIR / output_filename

                # Instantiate processor
                processor = ObjectProcessor(
                    input_video_path=str(video_path),
                    detection_type=detection_type,
                    verbose=True
                )
                # Attempt to gate to a parsed time window if present
                duration = _get_video_duration_seconds(video_path)
                rng = _parse_location_range(zoom_location, duration) or _parse_location_range(prompt, duration)
                if rng and hasattr(processor, 'set_zoom_time_segments'):
                    s, e = rng
                    if e > s:
                        print(f"⏱️ Applying zoom in range: {s:.2f}s→{e:.2f}s")
                        processor.set_zoom_time_segments([(s, e)])
                processor.enable_object_zoom(zoom_factor=3.5 if is_face else 2.0)
                if hasattr(processor, 'enable_debug_overlay'):
                    processor.enable_debug_overlay(False)
                if detection_type == "faces":
                    try:
                        print(f"🧠 Face backend: {getattr(processor, 'face_backend', 'unknown')}")
                    except Exception:
                        pass
                success = processor.process_and_save(str(output_path))
                if success and output_path.exists():
                    print(f"✅ ObjectProcessor zoom completed. Output: {output_path}")
                    # Generate an H.264/AAC web-friendly MP4 if needed
                    try:
                        info = ffmpeg_utils.get_media_info(str(output_path))
                        vcodec = None
                        acodec = None
                        if info.get('success'):
                            fmt = info.get('info', {}).get('format', {})
                            # Attempt to inspect stream codecs
                            for s in info.get('info', {}).get('streams', []) or []:
                                if s.get('codec_type') == 'video':
                                    vcodec = s.get('codec_name')
                                if s.get('codec_type') == 'audio':
                                    acodec = s.get('codec_name')
                        needs_convert = False
                        if vcodec is None or vcodec.lower() not in { 'h264', 'avc1' }:
                            needs_convert = True
                        if acodec is None or acodec.lower() not in { 'aac', 'mp4a' }:
                            needs_convert = True
                        if needs_convert:
                            conv_name = f"web_{output_filename}"
                            conv_path = OUTPUT_DIR / conv_name
                            print(f"🔄 Converting to web-friendly MP4: {conv_path}")
                            conv_res = ffmpeg_utils.convert_video(str(output_path), str(conv_path), video_codec="libx264", audio_codec="aac", quality="23")
                            if conv_res.get('success') and conv_path.exists():
                                output_filename_converted = conv_name
                            else:
                                output_filename_converted = output_filename
                        else:
                            output_filename_converted = output_filename
                    except Exception as _conv_err:
                        print(f"⚠️ Convert check failed: {_conv_err}")
                        output_filename_converted = output_filename

                    final_name = output_filename_converted
                    final_url = f"/api/outputs/{final_name}"
                    # Final sanity: verify playability and log codecs
                    try:
                        finfo = ffmpeg_utils.get_media_info(str(OUTPUT_DIR / final_name))
                        print(f"🧪 Final media info success={finfo.get('success')}")
                        if finfo.get('success'):
                            for s in finfo.get('info', {}).get('streams', []) or []:
                                print(f"  • stream {s.get('index')}: {s.get('codec_type')} {s.get('codec_name')} {s.get('pix_fmt', '')}")
                    except Exception as _e:
                        print(f"⚠️ Final media info check failed: {_e}")
                    return {
                        "type": "specific",
                        "commands": commands_text,
                        "status": "completed",
                        "output_file": final_name,
                        "output_path": str(OUTPUT_DIR / final_name),
                        "output_url": final_url,
                        "success": True
                    }
                else:
                    print("❌ ObjectProcessor zoom failed or output missing; falling back to effects if needed")
            except Exception as e:
                print(f"❌ Error during direct zoom handling: {e}")

        if not instances:
            print("❌ No valid commands extracted")
            return {
                "type": "specific", 
                "commands": commands_text, 
                "status": "error",
                "error": "No valid commands could be extracted from the prompt"
            }
        
        # Step 2: Generate timestamps using robust parsing that combines front/back cuts and ranges
        print("🔍 Starting timestamp extraction...")
        
        video_duration = _get_video_duration_seconds(video_path)
        edit_commands = {}
        for command, location in instances:
            cmd_lower = command.lower()
            if "trim" in cmd_lower or "cut" in cmd_lower or "splice" in cmd_lower:
                rng = infer_trim_range_from_prompt_and_instances(prompt, instances, video_duration)
                if rng is not None:
                    edit_commands[command] = [rng[0], rng[1]]
                else:
                    # As a last resort, try location-only inference
                    loc_rng = _parse_location_range(location, video_duration)
                    if loc_rng is not None:
                        edit_commands[command] = [loc_rng[0], loc_rng[1]]
                    else:
                        print("⚠️ Skipping trim command because no timing could be inferred")
                        continue
            elif any(token in cmd_lower for token in ["keep", "keep only", "keep part", "keep segment"]):
                # Keyword-based keep instructions, e.g., "keep only the part where he says elephant"
                # Extract a plausible keyword from prompt/location
                # Simple heuristic: look for 'says <word>' or 'saying <word>'
                kw = None
                m = re.search(r'\b(?:says|saying|mentions|said)\s+([a-zA-Z0-9\-]+)', (location or '') + ' ' + (prompt or ''), re.IGNORECASE)
                if m:
                    kw = m.group(1)
                else:
                    # fallback: last quoted token
                    m = re.findall(r'"([^"]+)"|\'([^\']+)\'', (location or '') + ' ' + (prompt or ''))
                    if m:
                        last = m[-1]
                        kw = last[0] or last[1]
                if kw:
                    segs = _find_keyword_segments_in_audio(video_path, kw)
                    if segs:
                        # Keep the first matched segment for now (could be extended to concatenate)
                        s, e = segs[0]
                        edit_commands[command] = [s, e]
                    else:
                        print(f"⚠️ No keyword hits found for '{kw}'")
                        continue
                else:
                    print("⚠️ Could not extract keyword from keep instruction")
                    continue
            else:
                if video_duration is not None:
                    edit_commands[command] = [0, float(video_duration)]
                else:
                    print("⚠️ Unknown duration; cannot set timing for non-trim command. Skipping.")
                    continue
        
        print(f"⏰ Generated timestamps: {edit_commands}")
        
        # Step 3: Execute edits (adapted from run_edits in specific.py)
        output_files = []
        current_video_path = video_path
        base_name = os.path.splitext(video_path)[0]
        
        # Generate proper output filename with ai_edited prefix
        timestamp = int(time.time())
        video_path_obj = Path(video_path)
        video_id = video_path_obj.stem
        output_filename = f"ai_edited_{video_id[:8]}_{timestamp}.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        # Execute the first command (for now, we'll handle one command at a time)
        if edit_commands:
            first_command = list(edit_commands.keys())[0]
            timestamps = edit_commands[first_command]
            
            print(f"🔧 Executing command: {first_command} with timestamps: {timestamps}")
            
            # Handle trim commands
            if "trim" in first_command.lower() or "cut" in first_command.lower():
                start_seconds = timestamps[0]
                duration_seconds = timestamps[1] - timestamps[0]
                
                start_time = f"{int(start_seconds//3600):02d}:{int((start_seconds%3600)//60):02d}:{start_seconds%60:06.3f}"
                duration_time = f"{int(duration_seconds//3600):02d}:{int((duration_seconds%3600)//60):02d}:{duration_seconds%60:06.3f}"
                
                print(f"✂️ Trimming from {start_time} for duration {duration_time}")
                
                result = ffmpeg_utils.trim_video(
                    str(current_video_path),
                    str(output_path),
                    start_time,
                    duration_time,
                    precise=True
                )
                
                if result.get("success"):
                    print(f"✅ Trim completed successfully")
                    output_files.append(output_filename)
                else:
                    print(f"❌ Trim failed: {result.get('error')}")
                    return {
                        "type": "specific",
                        "commands": commands_text,
                        "status": "error",
                        "error": f"Trim failed: {result.get('error')}"
                    }
            
            # Handle other commands (can be expanded)
            else:
                # Try speed up / slow down first
                loc_text = ""
                try:
                    for _cmd, _loc in instances:
                        if _cmd.strip().lower() == first_command.strip().lower():
                            loc_text = _loc or ""
                            break
                except Exception:
                    loc_text = ""
                speed_factor = _parse_speed_factor(f"{first_command} {loc_text} {prompt}")
                if speed_factor is not None:
                    print(f"🎞️ Applying speed effect {speed_factor}x for command: {first_command}")
                    # If a subrange was inferred, trim first then apply speed
                    input_for_effects = str(current_video_path)
                    start_seconds = timestamps[0]
                    end_seconds = timestamps[1]
                    duration_seconds = end_seconds - start_seconds
                    needs_segment = start_seconds > 0.001 or (video_duration is not None and end_seconds < float(video_duration) - 0.001)
                    tmp_segment_path = None
                    if needs_segment:
                        tmp_segment_path = str(OUTPUT_DIR / f"tmp_speed_segment_{int(time.time())}.mp4")
                        start_time_str = f"{int(start_seconds//3600):02d}:{int((start_seconds%3600)//60):02d}:{start_seconds%60:06.3f}"
                        duration_time_str = f"{int(duration_seconds//3600):02d}:{int((duration_seconds%3600)//60):02d}:{duration_seconds%60:06.3f}"
                        print(f"✂️ Pre-trimming segment {start_time_str} for {duration_time_str} before speed effect")
                        trim_res = ffmpeg_utils.trim_video(
                            str(current_video_path),
                            tmp_segment_path,
                            start_time_str,
                            duration_time_str,
                            precise=True
                        )
                        if trim_res.get("success"):
                            input_for_effects = tmp_segment_path
                        else:
                            print(f"⚠️ Pre-trim failed, applying speed to full video: {trim_res.get('error')}")
                            tmp_segment_path = None
                    result = ffmpeg_utils.apply_video_effects(
                        input_for_effects,
                        str(output_path),
                        effects={
                            "speed": float(speed_factor),
                            "audio_tempo": float(speed_factor)
                        }
                    )
                    # Clean up temp segment if created
                    if tmp_segment_path and os.path.exists(tmp_segment_path):
                        try:
                            os.remove(tmp_segment_path)
                        except Exception:
                            pass
                else:
                    # For other commands, apply basic enhancement
                    print(f"🎨 Applying default enhancement for command: {first_command}")
                    result = ffmpeg_utils.apply_video_effects(
                        str(current_video_path),
                        str(output_path),
                        effects={
                            "contrast": 1.1,
                            "saturation": 1.05
                        }
                    )
                
                if result.get("success"):
                    print(f"✅ Effects applied successfully")
                    output_files.append(output_filename)
                else:
                    print(f"❌ Effects failed: {result.get('error')}")
                    return {
                        "type": "specific",
                        "commands": commands_text,
                        "status": "error",
                        "error": f"Effects failed: {result.get('error')}"
                    }
        
        if output_files:
            return {
                "type": "specific",
                "commands": commands_text,
                "status": "completed",
                "output_file": output_files[0],
                "output_path": str(output_path),
                "success": True
            }
        else:
            return {
                "type": "specific",
                "commands": commands_text,
                "status": "error",
                "error": "No output files generated (no valid timing parsed; avoid falling back to 10s)"
            }
            
    except Exception as e:
        print(f"❌ Error in specific processing: {str(e)}")
        return {
            "type": "specific",
            "commands": prompt,
            "status": "error", 
            "error": f"Processing exception: {str(e)}"
        }

async def blur_object_in_video(input_path: str, output_path: str, target_object: str, start_time: str = None, duration: str = None):
    """Blur specific object in video using ObjectProcessor"""
    try:
        print(f"🎭 Starting face/object blur processing...")
        print(f"  Input: {input_path}")
        print(f"  Output: {output_path}")
        print(f"  Target: {target_object}")
        
        # Import ObjectProcessor (support both package and script run)
        try:
            from .object import ObjectProcessor
        except ImportError:
            from object import ObjectProcessor
        # Log where ObjectProcessor is imported from
        try:
            import inspect
            print(f"🧩 Using ObjectProcessor from: {inspect.getsourcefile(ObjectProcessor)}")
        except Exception:
            pass
        
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"❌ Input file not found: {input_path}")
            return {"success": False, "message": f"Input file not found: {input_path}"}
        
        # Determine detection type based on target object
        detection_type = "faces" if "face" in target_object.lower() else "objects"
        
        # Initialize ObjectProcessor with face detection for face blur
        processor = ObjectProcessor(
            input_video_path=input_path,
            detection_type=detection_type,
            verbose=True
        )
        
        # Enable blur with VERY strong blur strength
        processor.enable_object_blur(blur_strength=99)  # Maximum blur
        
        print(f"💥 STRONG blur enabled with strength 99!")
        
        # Process and save
        success = processor.process_and_save(output_path)
        
        if success and os.path.exists(output_path):
            print(f"✅ Face/object blur completed successfully!")
            print(f"📁 Output file created: {output_path}")
            file_size = os.path.getsize(output_path)
            print(f"📊 File size: {file_size} bytes")
            return {"success": True, "message": f"Successfully blurred {target_object} in video"}
        else:
            print(f"❌ Processing failed or output file not created")
            print(f"❌ Expected output: {output_path}")
            print(f"❌ File exists: {os.path.exists(output_path)}")
            return {"success": False, "message": f"Failed to process {target_object} blur"}
            
    except Exception as e:
        print(f"❌ Error in blur_object_in_video: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error: {str(e)}"}

async def zoom_to_object_in_video(input_path: str, output_path: str, target_object: str, start_time: str = None, duration: str = None, zoom_factor: float = 2.0):
    """Zoom to specific object in video using ObjectProcessor"""
    try:
        print(f"🔍 Starting object zoom processing...")
        print(f"  Input: {input_path}")
        print(f"  Output: {output_path}")
        print(f"  Target: {target_object}")
        print(f"  Zoom Factor: {zoom_factor}")
        
        # Import ObjectProcessor (support both package and script run)
        try:
            from .object import ObjectProcessor
        except ImportError:
            from object import ObjectProcessor
        
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"❌ Input file not found: {input_path}")
            return {"success": False, "message": f"Input file not found: {input_path}"}
        
        # Determine detection type based on target object
        detection_type = "faces" if "face" in target_object.lower() else "objects"
        
        # Initialize ObjectProcessor
        processor = ObjectProcessor(
            input_video_path=input_path,
            detection_type=detection_type,
            verbose=True
        )
        
        # Enable zoom to object
        processor.enable_object_zoom(zoom_factor=zoom_factor)
        # Enable debug overlay for verification
        if hasattr(processor, 'enable_debug_overlay'):
            processor.enable_debug_overlay(False)
        
        # Process and save
        success = processor.process_and_save(output_path)
        
        if success and os.path.exists(output_path):
            print(f"✅ Object zoom completed successfully!")
            return {"success": True, "message": f"Successfully zoomed to {target_object} in video"}
        else:
            print(f"❌ Processing failed or output file not created")
            return {"success": False, "message": f"Failed to process {target_object} zoom"}
            
    except Exception as e:
        print(f"❌ Error in zoom_to_object_in_video: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error: {str(e)}"}

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
