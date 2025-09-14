# The purpose of this file is to create commands upon the vague user prompt.

import cohere
import os
from dotenv import load_dotenv

def intent_generation():
    load_dotenv()
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("Error: COHERE_API_KEY not found in .env file.")
        return
    co = cohere.ClientV2(api_key)
    user_input = input("Describe your video edit request: ")
    prompt = ("You are given a very vague video edit request. Using the following detailed summary of the video, please categorize different edits that can be done to fulfill the user's request. Please categorize the video edit commands in exactly the following format with no other additions: <explaincommand> AND <where in the video/audio it should be applied>, <command>, <where in the video/audio it should be applied> and so on. If there are no specific commands, reply with 'No specific commands found'. Here is the user request: " + f"'{user_input}'. + Here is the detailed summary of the video: " + f"'{res_summary.summary}' " + "These are the different edit techniques that you can offer: clip trimming, transitions, audio effects, dynamic zoom, object face blur, face/object tracking, subtitles, video effects.")
    response = co.chat(
        model="command-a-03-2025",
        messages=[{"role": "user", "content": prompt}]
    )
    if hasattr(response, 'text'):
        response = response.text.strip()
    elif hasattr(response, 'message') and hasattr(response.message, 'content'):
        for item in response.message.content:
            if hasattr(item, 'text'):
                response = item.text.strip()
    
    edit_demands = response.split(',')
    for i in range(len(edit_demands)):
        edit_demands[i] = edit_demands[i].split(' AND ')
    print(edit_demands)



# Uses the Twelve Labs API to get a summary for every 10 seconds of the video
def get_segmented_summaries_twelvelabs(video_path, segment_duration=10):
    """
    Uploads the video to Twelve Labs, then gets a summary for each 10-second segment using the video ID.
    """
    import cv2
    import math
    import os
    from twelvelabs import TwelveLabs
    import time

    load_dotenv()
    
    # Validate video file
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return []
    
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
    print(f"Video file size: {file_size:.2f} MB")
    
    if file_size > 2048:  # TwelveLabs limit is 2GB
        print("Error: Video file too large (max 2GB)")
        return []
    
    # Load video to get duration and validate
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video file {video_path}")
        print("This might indicate the video is corrupted or in an unsupported format")
        return []
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if fps <= 0 or total_frames <= 0:
        print("Error: Invalid video properties detected")
        cap.release()
        return []
    
    duration = total_frames / fps
    num_segments = math.ceil(duration / segment_duration)
    cap.release()
    
    print(f"Video info: {width}x{height}, {fps:.2f}fps, {duration:.1f}s, will create {num_segments} segments")
    
    # Check duration limits (TwelveLabs: 4s - 3600s for Pegasus)
    if duration < 4:
        print("Error: Video too short (minimum 4 seconds)")
        return []
    if duration > 3600:
        print("Error: Video too long (maximum 1 hour for Pegasus)")
        return []

    # Setup Twelve Labs client - try multiple API key names
    api_key = os.getenv("TWELVE_LABS_API_KEY") or os.getenv("api_key_1")
    if not api_key:
        print("Error: TWELVE_LABS_API_KEY or api_key_1 not found in .env file.")
        return []
    client = TwelveLabs(api_key=api_key)

    # Get or create index
    try:
        from twelvelabs.indexes import IndexesCreateRequestModelsItem
        
        indexes = client.indexes.list()
        index_list = list(indexes)
        if len(index_list) > 0:
            index = index_list[0]
        else:
            print("No indexes found. Creating new index...")
            index = client.indexes.create(
                index_name="video-segmentation-index",
                models=[
                    IndexesCreateRequestModelsItem(
                        model_name="pegasus1.2",
                        model_options=["visual", "audio"]
                    )
                ]
            )
        print(f"Using index: ID={index.id}")
    except Exception as e:
        print(f"Error getting/creating index: {e}")
        return []

    # Upload video - no existing video logic, upload or fail
    try:
        print("🎬 Starting video upload (no fallback to existing videos)...")
        
        if not index.id:
            raise RuntimeError("No valid index ID")
        
        # Try the original video first, then the fixed version
        videos_to_try = [video_path]
        if not video_path.endswith("_fixed.mp4"):
            fixed_video = fix_video_for_upload(video_path)
            if fixed_video:
                videos_to_try.append(fixed_video)
        
        upload_success = False
        for try_video in videos_to_try:
            try:
                print(f"📤 Attempting upload: {try_video}")
                
                # Use the working approach - open file as binary
                with open(try_video, "rb") as f:
                    task = client.tasks.create(index_id=index.id, video_file=f)
                print(f"✅ Upload task created: {task.id}")
                
                # Wait for upload to complete
                if task.id:
                    print("⏳ Waiting for upload to complete...")
                    task = client.tasks.wait_for_done(task_id=task.id, callback=lambda t: print(f"Status: {t.status}"))
                    if task.status == "ready":
                        video_id = task.video_id
                        print(f"🎉 Video uploaded successfully! Video ID: {video_id}")
                        upload_success = True
                        break
                    else:
                        print(f"❌ Upload failed with status: {task.status}")
                else:
                    print("❌ Failed to create upload task")
            except Exception as upload_error:
                print(f"❌ Upload attempt failed: {upload_error}")
                continue
        
        if not upload_success:
            raise RuntimeError("💥 ALL UPLOAD ATTEMPTS FAILED! Cannot proceed without uploading video.")
            
    except Exception as e:
        print(f"💥 FATAL ERROR: {e}")
        print("🚫 No existing video fallback - upload is required!")
        return []

    summaries = []
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, duration)
        prompt = f"Provide a detailed summary of what happens in this specific {segment_duration}-second segment from {start_time:.1f}s to {end_time:.1f}s. Focus only on this time range."
        
        try:
            print(f"Getting summary for segment {i+1}: {start_time:.1f}s - {end_time:.1f}s")
            if video_id:
                response = client.summarize(
                    video_id=video_id,
                    type="summary",
                    prompt=prompt
                )
                
                # Since we're using type="summary", the response should have summary attribute
                if response.summarize_type == "summary":
                    summary_text = response.summary
                elif response.summarize_type == "chapter":
                    summary_text = str(response.chapters)
                elif response.summarize_type == "highlight":
                    summary_text = str(response.highlights)
                else:
                    summary_text = "No summary available"
                    
                summaries.append(f"Segment {i+1} ({start_time:.1f}s-{end_time:.1f}s): {summary_text}")
            else:
                summaries.append(f"Segment {i+1}: Error - No video ID available")
        except Exception as e:
            error_msg = f"Error summarizing segment {i+1}: {e}"
            print(error_msg)
            summaries.append(error_msg)
    
    return summaries

def run_edits(timestamp, commands):
    pass

def fix_video_for_upload(input_path, output_path=None):
    """
    Re-encode video to fix potential corruption issues for TwelveLabs upload
    """
    import subprocess
    
    if output_path is None:
        name, ext = os.path.splitext(input_path)
        output_path = f"{name}_fixed.mp4"  # Force MP4 format
    
    # Try multiple encoding strategies
    strategies = [
        {
            "name": "Standard H.264/AAC",
            "cmd": [
                "ffmpeg", "-i", input_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",       # Ensure compatible pixel format
                "-r", "30",                  # Standard frame rate
                "-movflags", "+faststart",
                "-strict", "experimental",
                "-y", output_path
            ]
        },
        {
            "name": "Conservative re-encode",
            "cmd": [
                "ffmpeg", "-i", input_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "slow",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-profile:v", "baseline",    # Most compatible H.264 profile
                "-level", "3.0",
                "-movflags", "+faststart",
                "-y", output_path
            ]
        },
        {
            "name": "Force reconstruction",
            "cmd": [
                "ffmpeg", "-i", input_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "medium",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=1280:720",     # Standard resolution
                "-r", "25",                  # Standard PAL frame rate
                "-ar", "44100",              # Standard audio sample rate
                "-ac", "2",                  # Stereo audio
                "-movflags", "+faststart",
                "-y", output_path
            ]
        }
    ]
    
    for strategy in strategies:
        try:
            print(f"Trying: {strategy['name']}")
            subprocess.run(strategy["cmd"], check=True, capture_output=True, text=True)
            
            # Verify the output file
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                print(f"✅ Successfully created: {output_path}")
                return output_path
            else:
                print(f"❌ Output file invalid or too small")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {e}")
            continue
        except FileNotFoundError:
            print("❌ FFmpeg not found. Please install FFmpeg.")
            return None
    
    print("❌ All encoding strategies failed")
    return None

def test_video_upload(video_path):
    """Test video upload functionality specifically"""
    import cv2
    from twelvelabs import TwelveLabs
    from twelvelabs.indexes import IndexesCreateRequestModelsItem
    
    load_dotenv()
    
    print(f"🧪 Testing video upload for: {video_path}")
    
    # Setup client
    api_key = os.getenv("TWELVE_LABS_API_KEY")
    if not api_key:
        print("Error: TWELVELABS_API_KEY not found")
        return False
    client = TwelveLabs(api_key=api_key)
    
    # Get index
    indexes = client.indexes.list()
    index_list = list(indexes)
    if len(index_list) > 0:
        index = index_list[0]
        print(f"Using index: {index.id}")
    else:
        print("No index found")
        return False
    
    # Try upload using the working method from vague_or_nah.py
    try:
        print("Trying file upload with binary file handle...")
        if index.id:
            # Open file as binary like in vague_or_nah.py
            with open(video_path, "rb") as f:
                task = client.tasks.create(index_id=index.id, video_file=f)
            print(f"Task created: {task.id}")
            
            if task.id:
                print("Waiting for processing...")
                task = client.tasks.wait_for_done(task_id=task.id, callback=lambda t: print(f"Status: {t.status}"))
                
                if task.status == "ready":
                    print(f"✅ SUCCESS! Video ID: {task.video_id}")
                    return True
                else:
                    print(f"❌ Upload failed with status: {task.status}")
            else:
                print("❌ Failed to create upload task")
        
        return False
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        print("This might be due to:")
        print("   - Invalid API key or permissions")
        print("   - Account limits reached") 
        print("   - Network connectivity issues")
        print("   - Video file format incompatibility")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test_upload":
        # Test upload mode
        video_path = "output_test_clean.mp4"
        test_video_upload(video_path)
        exit()
    
    # Normal segmented summaries mode
    # Try multiple video files
    possible_videos = [
        "output_test_clean.mp4",        # Clean test video we just created
        "output_converted1.mp4",
        "output_converted1_edited.mp4", 
        "output_converted1_fixed.mp4"
    ]
    
    # Find a working video file
    original_video = None
    for video in possible_videos:
        if os.path.exists(video):
            original_video = video
            print(f"Found video file: {video}")
            break
    
    if not original_video:
        print("❌ No video files found! Please make sure you have:")
        for video in possible_videos:
            print(f"   - {video}")
        exit(1)
    
    # Check if video is already in a good format
    print(f"\nStep 1: Analyzing video file: {original_video}")
    import cv2
    cap = cv2.VideoCapture(original_video)
    if cap.isOpened():
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        cap.release()
        
        print(f"Current format: {codec}, {width}x{height}, {fps:.2f}fps")
        
        # Check if it needs fixing
        needs_fixing = (
            codec not in ['avc1', 'h264'] or  # Not H.264
            fps > 60 or fps < 10 or           # Unusual frame rate
            width > 1920 or height > 1080     # Too high resolution
        )
        
        if needs_fixing:
            print("🔧 Video needs re-encoding for TwelveLabs compatibility")
            fixed_video = fix_video_for_upload(original_video)
            video_path = fixed_video if fixed_video else original_video
        else:
            print("✅ Video format looks compatible")
            video_path = original_video
    else:
        print("🔧 Cannot read video, attempting to fix...")
        fixed_video = fix_video_for_upload(original_video)
        video_path = fixed_video if fixed_video else original_video
    
    print(f"\nStep 2: Testing segmented summaries with: {video_path}")
    summaries = get_segmented_summaries_twelvelabs(video_path)
    print("\n" + "="*50)
    print("SEGMENTED SUMMARIES RESULTS")
    print("="*50)
    if summaries:
        for summary in summaries:
            print(summary)
    else:
        print("❌ No summaries generated. Check the errors above.")