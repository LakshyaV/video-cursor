# The purpose of this file is to extract time stamps of specific instances from the video and run commands to edit those specific instances.

import cohere
import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem
from twelvelabs.tasks import TasksRetrieveResponse
from glob import glob
import vague_or_nah
import utils
import output_utils
import object
load_dotenv()

index, vid_path = vague_or_nah.upload_video()

def intent_extraction():
    load_dotenv()
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("Error: COHERE_API_KEY not found in .env file.")
        return
    co = cohere.Client(api_key)
    user_input = input("Describe your video edit request: ")
    prompt = (
    "Extract the specific video edit commands from the following user request. "
    "Output them **only** in this exact format: "
    "<command> AND <where in the video/audio it should be applied>, "
    "<command> AND <where in the video/audio it should be applied>, "
    "… (continue as needed). "
    "Do not include section titles, explanations, or any extra text—just the commands in the specified format. "
    "Here is the user request: '" + user_input + "'. "
    "Available edit techniques: clip trimming, transitions, audio effects, dynamic zoom, face zoom, object face blur, "
    "face/object tracking, subtitles, add subtitles, video effects, apply video effects, blur, saturation, "
    "brightness, contrast, artistic filters, sound effects (boom, gunshot, explosion, whoosh), splice."
    )
    response = co.chat(
        model="command-r-plus",
        message=prompt
    )
    if hasattr(response, 'text'):
        response = response.text.strip()
    elif hasattr(response, 'message') and hasattr(response.message, 'content'):
        for item in response.message.content:
            if hasattr(item, 'text'):
                response = item.text.strip()
    
    print(response)
    
    edits = response.split(",")
    
    result = []
    for edit in edits:
        parts = edit.strip().split("AND")
        if len(parts) == 2:
            command = parts[0].strip()
            location = parts[1].strip()
            result.append([command, location])
    print(result)
    return result

def timestamp_extraction(instances, vid_path):
    edit_demand_final = {}
    client = TwelveLabs(api_key=os.getenv("api_key_1"))

    for i in range(len(instances)):
        query = "Find " + instances[i][1]
        print(query)
        search_results = client.search.query(
            index_id=index.id,
            query_text=query,
            search_options=["visual", "audio"]
        )
        print("Search results type:", type(search_results))
        print("Search results:", search_results)
        
        # Convert SyncPager to list to get all results
        clips = list(search_results)
        print(f"Found {len(clips)} clips")
        
        for clip in clips:
            print(f"Found clip: start={clip.start}s, end={clip.end}s, score={clip.score}")
            edit_demand_final[instances[i][0]] = [clip.start, clip.end]
            break
    return edit_demand_final

def zoom_to_object(input_video_path, output_video_path, target_object, start_time=None, duration=None, zoom_factor=2.0):
    """
    Zoom into a specific object in the video.
    
    Args:
        input_video_path (str): Path to input video
        output_video_path (str): Path to output video
        target_object (str): Object to zoom into (e.g., "person", "car", "colonel")
        start_time (str): Start time in HH:MM:SS format (optional)
        duration (str): Duration in HH:MM:SS format (optional)
        zoom_factor (float): Zoom level (default 2.0)
        
    Returns:
        dict: Result with success status and output/error messages
    """
    try:
        print(f"🎯 Zooming into '{target_object}' with factor {zoom_factor}")
        
        # Create object processor
        processor = object.ObjectProcessor(
            input_video_path=input_video_path,
            detection_type="objects",  # Use object detection
            target_classes=[target_object] if target_object in ["person", "car", "dog", "cat"] else None,
            verbose=True
        )
        
        # Enable zoom
        processor.enable_object_zoom(zoom_factor=zoom_factor)
        
        # If specific time range is provided, we need to handle it differently
        if start_time and duration:
            print(f"⚠️  Time-specific zoom not fully supported yet. Processing entire video.")
            print(f"   Target: {target_object}, Start: {start_time}, Duration: {duration}")
        
        # Process and save video
        success = processor.process_and_save(output_video_path)
        
        if success:
            return {"success": True, "output": f"Object zoom completed successfully"}
        else:
            return {"success": False, "error": "Object zoom processing failed"}
            
    except Exception as e:
        return {"success": False, "error": f"Object zoom error: {str(e)}"}

def zoom_to_face(input_video_path, output_video_path, target_person=None, start_time=None, duration=None, zoom_factor=3.5):
    """
    Zoom into a specific person's face in the video using advanced face detection.
    
    Args:
        input_video_path (str): Path to input video
        output_video_path (str): Path to output video  
        target_person (str): Name of person to zoom into (e.g., "stark", "colonel", "person")
        start_time (str): Start time in HH:MM:SS format (optional)
        duration (str): Duration in HH:MM:SS format (optional)
        zoom_factor (float): Zoom level for face (default 2.5)
        
    Returns:
        dict: Result with success status and output/error messages
    """
    try:
        print(f"👤 Zooming into face of '{target_person}' with factor {zoom_factor}")
        
        # Create face processor for face detection
        processor = object.ObjectProcessor(
            input_video_path=input_video_path,
            detection_type="faces",  # Use face detection
            verbose=True
        )
        
        # Enable zoom with higher factor for faces (faces need more zoom to be visible)
        processor.enable_object_zoom(zoom_factor=zoom_factor)
        
        # If we need to identify a specific person, we can extract faces first
        if target_person and target_person.lower() not in ["person", "face", "anyone"]:
            print(f"🔍 Extracting faces to identify '{target_person}'...")
            
            # Extract unique faces from the video
            face_ids = processor.extract_objects(output_folder="detected_faces", sample_frames=20)
            
            if face_ids:
                print(f"✅ Found {len(face_ids)} unique faces")
                print("💡 For now, zooming into the most prominent face")
                print(f"   To zoom into a specific person, you can manually select from detected_faces/ folder")
                
                # For now, we'll zoom into the most prominent face
                # In the future, you could add face recognition to match specific people
            else:
                print("⚠️  No faces detected, falling back to person detection")
                # Fallback to person detection
                processor = object.ObjectProcessor(
                    input_video_path=input_video_path,
                    detection_type="objects",
                    target_classes=["person"],
                    verbose=True
                )
                processor.enable_object_zoom(zoom_factor=zoom_factor)
        
        # If specific time range is provided, trim the segment first then apply face zoom
        if start_time and duration:
            print(f"🎯 Applying face zoom to specific segment: {start_time} for {duration}")
            
            import tempfile
            import os
            
            # Create temporary file for trimmed segment
            temp_trimmed = tempfile.mktemp(suffix="_face_segment.mp4")
            
            try:
                # Step 1: Trim to the specific segment
                print("Step 1: Trimming to target segment...")
                trim_result = utils.trim_video(
                    input_path=input_video_path,
                    output_path=temp_trimmed,
                    start_time=start_time,
                    duration=duration,
                    precise=True
                )
                
                if not trim_result["success"]:
                    return {"success": False, "error": f"Failed to trim segment: {trim_result['error']}"}
                
                # Step 2: Apply face zoom to the trimmed segment
                print("Step 2: Applying face zoom to segment...")
                processor_segment = object.ObjectProcessor(
                    input_video_path=temp_trimmed,
                    detection_type="faces",
                    verbose=True
                )
                
                # Use higher zoom factor for better visibility
                processor_segment.enable_object_zoom(zoom_factor=zoom_factor * 1.5)  # Increase zoom
                
                # Process the trimmed segment
                success = processor_segment.process_and_save(output_video_path)
                
                # Ensure processor is properly cleaned up
                del processor_segment
                
                # Add a small delay to ensure file handles are released
                import time
                time.sleep(0.5)
                
                # Clean up temporary file with retry logic
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if os.path.exists(temp_trimmed):
                            os.remove(temp_trimmed)
                        break
                    except PermissionError:
                        if attempt < max_attempts - 1:
                            print(f"Retrying cleanup attempt {attempt + 1}...")
                            time.sleep(1)
                        else:
                            print(f"⚠️  Could not delete temporary file: {temp_trimmed}")
                            print("   This file can be manually deleted later.")
                    
            except Exception as e:
                # Clean up on error with retry logic
                import time
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if os.path.exists(temp_trimmed):
                            os.remove(temp_trimmed)
                        break
                    except PermissionError:
                        if attempt < max_attempts - 1:
                            time.sleep(1)
                        else:
                            print(f"⚠️  Could not delete temporary file: {temp_trimmed}")
                raise e
                
        else:
            print("🎯 Processing entire video for face zoom...")
            # Process entire video with face tracking
            success = processor.process_and_save(output_video_path)
        
        if success:
            return {"success": True, "output": f"Face zoom completed successfully"}
        else:
            return {"success": False, "error": "Face zoom processing failed"}
            
    except Exception as e:
        return {"success": False, "error": f"Face zoom error: {str(e)}"}

def run_edits(commands, original_instances=None):
    output_files = []  # Store all output file paths
    current_video_path = vid_path  # Start with original video
    base_name = os.path.splitext(vid_path)[0]
    
    for i, (command, timestamps) in enumerate(commands.items()): 
        print(f"Running command {i+1}: {command} with timestamps: {timestamps}")
        print(f"Working with video: {current_video_path}")
        
        # Handle different command variations
        if command.lower() in ["clip trimming", "trim", "trimming"]:
            # Convert seconds to HH:MM:SS format
            start_seconds = timestamps[0]
            duration_seconds = timestamps[1] - timestamps[0]
            
            start_time = f"{int(start_seconds//3600):02d}:{int((start_seconds%3600)//60):02d}:{int(start_seconds%60):02d}"
            duration_time = f"{int(duration_seconds//3600):02d}:{int((duration_seconds%3600)//60):02d}:{int(duration_seconds%60):02d}"
            
            print(f"Trimming from {start_time} for duration {duration_time}")
            
            # Create output filename - use a consistent name for sequential edits
            if i == 0:
                # First edit - create new file
                output_path = f"{base_name}_edited.mp4"
            else:
                # Subsequent edits - overwrite the previous result
                output_path = f"{base_name}_edited.mp4"
            
            # Call the trim function
            result = utils.trim_video(
                input_path=current_video_path,
                output_path=output_path,
                start_time=start_time,
                duration=duration_time,
                precise=True  # Use precise trimming
            )
            
            if result["success"]:
                print(f"✅ Video trimmed successfully!")
                print(f"📁 Output file: {output_path}")
                print(f"📂 Full path: {os.path.abspath(output_path)}")
                
                # Check if file exists and get size
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                
                # Update current video path for next operation
                current_video_path = output_path
                # Add to output_files if this is the first successful operation or if output_files is empty
                if i == 0 or len(output_files) == 0:
                    output_files.append(output_path)
            else:
                print(f"❌ Error trimming video: {result['error']}")
                print(f"FFmpeg output: {result['output']}")
                print(f"FFmpeg error: {result['error']}")
        
        elif command.lower() in ["cut out", "splice", "remove", "delete", "cut", "splice out"]:
            print(f"✂️ Splicing out video section...")
            
            # Convert timestamps to time format
            start_seconds = timestamps[0]
            end_seconds = timestamps[1]
            
            start_time = f"{int(start_seconds//3600):02d}:{int((start_seconds%3600)//60):02d}:{int(start_seconds%60):02d}"
            end_time = f"{int(end_seconds//3600):02d}:{int((end_seconds%3600)//60):02d}:{int(end_seconds%60):02d}"
            
            print(f"Splicing out section from {start_time} to {end_time}")
            
            final_output = f"{base_name}_edited.mp4"
            
            # Use splice function to remove the specified section
            result = utils.splice_video(
                input_path=current_video_path,
                output_path=final_output,
                remove_start_time=start_time,
                remove_end_time=end_time
            )
            
            if result["success"]:
                print(f"✅ Video section spliced out successfully!")
                print(f"📁 Output file: {final_output}")
                print(f"📂 Full path: {os.path.abspath(final_output)}")
                
                # Check if file exists and get size
                if os.path.exists(final_output):
                    file_size = os.path.getsize(final_output)
                    print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                
                # Update current video path for next operation
                current_video_path = final_output
                # Add to output_files if this is the first successful operation or if output_files is empty
                if i == 0 or len(output_files) == 0:
                    output_files.append(final_output)
            else:
                print(f"❌ Error splicing video: {result['error']}")
                print(f"FFmpeg output: {result['output']}")
                print(f"FFmpeg error: {result['error']}")
        
        elif command.lower() in ["add sound effect", "sound effect", "boom effect", "add boom", "boom", "gunshot", "explosion", "whoosh", "swoosh"]:
            # Handle sound effect addition
            print(f"🔊 Adding sound effect...")
            
            # Determine which sound effect to use based on command
            sound_effect_mapping = {
                "boom": "boom_effect.mp3",
                "boom effect": "boom_effect.mp3", 
                "add boom": "boom_effect.mp3",
                "gunshot": "gunshot_effect.mp3",
                "explosion": "explosion_effect.mp3",
                "whoosh": "whoosh_effect.mp3",
                "swoosh": "swoosh_effect.mp3",
                "sound effect": "boom_effect.mp3",  # Default
                "add sound effect": "boom_effect.mp3"  # Default
            }
            
            # Find the appropriate sound effect file
            sound_effect_path = None
            for effect_type, file_path in sound_effect_mapping.items():
                if effect_type in command.lower():
                    if os.path.exists(file_path):
                        sound_effect_path = file_path
                        break
                    else:
                        print(f"⚠️  {file_path} not found, trying default...")
            
            # Fallback to boom_effect.mp3 if no specific effect found
            if not sound_effect_path:
                sound_effect_path = "boom_effect.mp3"
            
            # Check if sound effect file exists
            if not os.path.exists(sound_effect_path):
                print(f"⚠️  Sound effect file not found: {sound_effect_path}")
                print("Available sound effects: boom_effect.mp3, gunshot_effect.mp3, explosion_effect.mp3")
                print("Please add sound effect files to the project directory")
                continue
            
            print(f"Using sound effect: {sound_effect_path}")
            
            final_output = f"{base_name}_edited.mp4"
            
            # For sound effects, we need to determine timing
            if i == 0:
                # First operation - use the specific timestamps
                start_seconds = timestamps[0]
                duration_seconds = timestamps[1] - timestamps[0]
                effect_start_time = start_seconds  # Start effect at the beginning of the segment
                effect_duration = min(duration_seconds, 3.0)  # Limit effect duration to 3 seconds max
            else:
                # Subsequent operation - add effect to the entire current video
                effect_start_time = 0  # Start at beginning
                effect_duration = 3.0  # 3 second effect
            
            print(f"Adding sound effect at {effect_start_time}s for {effect_duration}s")
            
            # Add sound effect
            result = utils.add_sound_effect(
                input_path=current_video_path,
                output_path=final_output,
                effect_path=sound_effect_path,
                start_time=effect_start_time,
                duration=effect_duration,
                volume=1.0,
                replace=False  # Mix with original audio
            )
            
            if result["success"]:
                print(f"✅ Sound effect added successfully!")
                print(f"📁 Output file: {final_output}")
                print(f"📂 Full path: {os.path.abspath(final_output)}")
                
                # Check if file exists and get size
                if os.path.exists(final_output):
                    file_size = os.path.getsize(final_output)
                    print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                
                # Update current video path for next operation
                current_video_path = final_output
                # Add to output_files if this is the first successful operation or if output_files is empty
                if i == 0 or len(output_files) == 0:
                    output_files.append(final_output)
            else:
                print(f"❌ Error adding sound effect: {result['error']}")
                print(f"FFmpeg output: {result['output']}")
                print(f"FFmpeg error: {result['error']}")
        
        elif command.lower() in ["dynamic zoom", "zoom", "zoom effect", "zoom into", "zoom on"]:
            # Check if this is an object-based zoom request
            # Look for object names in the location part of the command
            location_text = ""
            if original_instances and i < len(original_instances):
                # Get the location text from the original instances
                location_text = original_instances[i][1] if len(original_instances[i]) > 1 else ""
            
            # Check for face-specific zoom requests
            face_keywords = ["face", "stark", "colonel", "person's face", "his face", "her face", "their face"]
            is_face_zoom = any(keyword.lower() in location_text.lower() for keyword in face_keywords)
            
            # Common objects that can be detected
            detectable_objects = [
                "person", "people", "man", "woman", "colonel", "soldier", "officer",
                "car", "truck", "bus", "motorcycle", "bicycle",
                "dog", "cat", "horse", "bird", "cow", "sheep",
                "face", "person's face", "human"
            ]
            
            # Check if location contains object names
            target_object = None
            for obj in detectable_objects:
                if obj.lower() in location_text.lower():
                    target_object = obj
                    break
            
            if target_object:
                final_output = f"{base_name}_edited.mp4"
                
                # Convert timestamps to time format if this is the first operation
                if i == 0:
                    start_seconds = timestamps[0]
                    duration_seconds = timestamps[1] - timestamps[0]
                    start_time = f"{int(start_seconds//3600):02d}:{int((start_seconds%3600)//60):02d}:{int(start_seconds%60):02d}"
                    duration_time = f"{int(duration_seconds//3600):02d}:{int((duration_seconds%3600)//60):02d}:{int(duration_seconds%60):02d}"
                else:
                    start_time = None
                    duration_time = None
                
                # Check if this is a face-specific zoom
                if is_face_zoom:
                    print(f"👤 Detected face zoom request: '{target_object}'")
                    
                    # Extract the person's name if mentioned
                    person_name = None
                    name_keywords = ["stark", "colonel", "officer", "soldier"]
                    for name in name_keywords:
                        if name.lower() in location_text.lower():
                            person_name = name
                            break
                    
                    # Use face-specific zoom
                    result = zoom_to_face(
                        input_video_path=current_video_path,
                        output_video_path=final_output,
                        target_person=person_name or target_object,
                        start_time=start_time,
                        duration=duration_time,
                        zoom_factor=4.0  # Higher zoom for faces
                    )
                else:
                    # Regular object-based zoom
                    print(f"🎯 Detected object-based zoom request: '{target_object}'")
                    
                    result = zoom_to_object(
                        input_video_path=current_video_path,
                        output_video_path=final_output,
                        target_object=target_object,
                        start_time=start_time,
                        duration=duration_time,
                        zoom_factor=2.0
                    )
                
                if result["success"]:
                    print(f"✅ Object zoom applied successfully!")
                    print(f"📁 Output file: {final_output}")
                    print(f"📂 Full path: {os.path.abspath(final_output)}")
                    
                    # Check if file exists and get size
                    if os.path.exists(final_output):
                        file_size = os.path.getsize(final_output)
                        print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                    
                    # Update current video path for next operation
                    current_video_path = final_output
                    # Add to output_files if this is the first successful operation or if output_files is empty
                    if i == 0 or len(output_files) == 0:
                        output_files.append(final_output)
                else:
                    print(f"❌ Error applying object zoom: {result['error']}")
            else:
                # Regular zoom (no specific object detected)
                print(f"🔍 No specific object detected, using regular zoom")
                
                if i == 0:
                    # First operation - need to trim the specific segment first
                    start_seconds = timestamps[0]
                    duration_seconds = timestamps[1] - timestamps[0]
                    
                    start_time = f"{int(start_seconds//3600):02d}:{int((start_seconds%3600)//60):02d}:{int(start_seconds%60):02d}"
                    duration_time = f"{int(duration_seconds//3600):02d}:{int((duration_seconds%3600)//60):02d}:{int(duration_seconds%60):02d}"
                    
                    print(f"Applying dynamic zoom from {start_time} for duration {duration_time}")
                    
                    # Create temporary trimmed file first
                    temp_trimmed = f"{base_name}_temp_trimmed_{int(start_seconds)}s_to_{int(timestamps[1])}s.mp4"
                    final_output = f"{base_name}_edited.mp4"
                    
                    # Step 1: Trim the segment
                    print("Step 1: Trimming segment...")
                    trim_result = utils.trim_video(
                        input_path=current_video_path,
                        output_path=temp_trimmed,
                        start_time=start_time,
                        duration=duration_time,
                        precise=True
                    )
                    
                    if not trim_result["success"]:
                        print(f"❌ Error trimming segment: {trim_result['error']}")
                        continue
                    
                    # Step 2: Apply zoom effect to the trimmed segment
                    print("Step 2: Applying zoom effect...")
                    zoom_result = utils.apply_video_effects(
                        input_path=temp_trimmed,
                        output_path=final_output,
                        zoom=True  # Enable zoom effect
                    )
                    
                    # Clean up temporary file
                    if os.path.exists(temp_trimmed):
                        os.remove(temp_trimmed)
                    
                    if zoom_result["success"]:
                        print(f"✅ Dynamic zoom applied successfully!")
                        print(f"📁 Output file: {final_output}")
                        print(f"📂 Full path: {os.path.abspath(final_output)}")
                        
                        # Check if file exists and get size
                        if os.path.exists(final_output):
                            file_size = os.path.getsize(final_output)
                            print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                        
                        # Update current video path for next operation
                        current_video_path = final_output
                        # Add to output_files if this is the first successful operation or if output_files is empty
                        if i == 0 or len(output_files) == 0:
                            output_files.append(final_output)
                    else:
                        print(f"❌ Error applying zoom: {zoom_result['error']}")
                        print(f"FFmpeg output: {zoom_result['output']}")
                        print(f"FFmpeg error: {zoom_result['error']}")
                else:
                    # Subsequent operation - apply zoom to entire current video
                    print("Applying zoom effect to entire current video...")
                    final_output = f"{base_name}_edited.mp4"
                    
                    zoom_result = utils.apply_video_effects(
                        input_path=current_video_path,
                        output_path=final_output,
                        zoom=True  # Enable zoom effect
                    )
                    
                    if zoom_result["success"]:
                        print(f"✅ Dynamic zoom applied successfully!")
                        print(f"📁 Output file: {final_output}")
                        print(f"📂 Full path: {os.path.abspath(final_output)}")
                        
                        # Check if file exists and get size
                        if os.path.exists(final_output):
                            file_size = os.path.getsize(final_output)
                            print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                        
                        # Update current video path for next operation
                        current_video_path = final_output
                        # Add to output_files if this is the first successful operation or if output_files is empty
                        if i == 0 or len(output_files) == 0:
                            output_files.append(final_output)
                    else:
                        print(f"❌ Error applying zoom: {zoom_result['error']}")
                        print(f"FFmpeg output: {zoom_result['output']}")
                        print(f"FFmpeg error: {zoom_result['error']}")
        
        elif command.lower() in ["add subtitles", "subtitles", "add subtitle", "subtitle", "transcribe", "auto subtitles", "generate subtitles"]:
            # Handle subtitle addition
            print(f"📝 Adding subtitles...")
            
            final_output = f"{base_name}_edited.mp4"
            
            # Check if there's a subtitle file available (.srt files in directory)
            srt_files = [f for f in os.listdir('.') if f.endswith('.srt')]
            
            if srt_files:
                # Use existing subtitle file
                subtitle_file = srt_files[0]  # Use the first .srt file found
                print(f"📄 Found subtitle file: {subtitle_file}")
                print(f"🔥 Burning subtitles into video...")
                
                result = utils.add_subtitles(
                    input_path=current_video_path,
                    output_path=final_output,
                    subtitle_path=subtitle_file,
                    burn=True  # Burn subtitles into video (hardcoded)
                )
                
                if result["success"]:
                    print(f"✅ Subtitles added successfully!")
                    print(f"📁 Output file: {final_output}")
                    print(f"📂 Full path: {os.path.abspath(final_output)}")
                    
                    # Check if file exists and get size
                    if os.path.exists(final_output):
                        file_size = os.path.getsize(final_output)
                        print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                    
                    # Update current video path for next operation
                    current_video_path = final_output
                    # Add to output_files if this is the first successful operation or if output_files is empty
                    if i == 0 or len(output_files) == 0:
                        output_files.append(final_output)
                else:
                    print(f"❌ Error adding subtitles: {result['error']}")
                    print(f"FFmpeg output: {result['output']}")
                    print(f"FFmpeg error: {result['error']}")
            else:
                # No subtitle file found - use automatic transcription
                print(f"🎤 No subtitle file found. Generating subtitles automatically...")
                print(f"🔄 Transcribing audio and burning subtitles into video...")
                
                # Use transcribe_audio function which automatically generates and burns subtitles
                result = utils.transcribe_audio(
                    input_path=current_video_path,
                    output_path=final_output,
                    language="en-US",  # Default to English
                    chunk_duration=30  # 30 second chunks for transcription
                )
                
                if result["success"]:
                    print(f"✅ Auto-generated subtitles added successfully!")
                    print(f"📁 Output file: {final_output}")
                    print(f"📂 Full path: {os.path.abspath(final_output)}")
                    
                    # Check if file exists and get size
                    if os.path.exists(final_output):
                        file_size = os.path.getsize(final_output)
                        print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                    
                    # Update current video path for next operation
                    current_video_path = final_output
                    # Add to output_files if this is the first successful operation or if output_files is empty
                    if i == 0 or len(output_files) == 0:
                        output_files.append(final_output)
                else:
                    print(f"❌ Error generating subtitles: {result['error']}")
                    if 'output' in result:
                        print(f"FFmpeg output: {result['output']}")
                    if 'error' in result:
                        print(f"Error details: {result['error']}")
        
        elif command.lower() in ["blur", "apply blur", "add blur", "saturation", "saturate", "brightness", "brighten", 
                               "contrast", "apply contrast", "video effects", "apply video effects", "artistic filter", 
                               "black and white", "sepia", "vintage", "negative", "emboss", "edge detection"]:
            # Handle video effects application
            print(f"🎨 Applying video effects...")
            
            # Determine which effect to apply based on command
            blur_amount = 0
            brightness_adjustment = 0
            contrast_adjustment = 1
            saturation_adjustment = 1
            artistic_filter = "none"
            
            command_lower = command.lower()
            
            # Parse the effect type from command
            if "blur" in command_lower:
                blur_amount = 3  # Default blur strength
                print(f"🔵 Applying blur effect (strength: {blur_amount})")
            elif "saturation" in command_lower or "saturate" in command_lower:
                saturation_adjustment = 1.5  # Increase saturation
                print(f"🌈 Applying saturation effect (level: {saturation_adjustment})")
            elif "brightness" in command_lower or "brighten" in command_lower:
                brightness_adjustment = 0.2  # Increase brightness
                print(f"☀️ Applying brightness effect (level: {brightness_adjustment})")
            elif "contrast" in command_lower:
                contrast_adjustment = 1.3  # Increase contrast
                print(f"🔆 Applying contrast effect (level: {contrast_adjustment})")
            elif "black and white" in command_lower or "black & white" in command_lower:
                artistic_filter = "black & white"
                print(f"⚫ Applying black & white filter")
            elif "sepia" in command_lower:
                artistic_filter = "sepia"
                print(f"🟤 Applying sepia filter")
            elif "vintage" in command_lower:
                artistic_filter = "vintage"
                print(f"📷 Applying vintage filter")
            elif "negative" in command_lower:
                artistic_filter = "negative"
                print(f"🔄 Applying negative filter")
            elif "emboss" in command_lower:
                artistic_filter = "emboss"
                print(f"🏔️ Applying emboss filter")
            elif "edge detection" in command_lower or "edge" in command_lower:
                artistic_filter = "edge detection"
                print(f"📐 Applying edge detection filter")
            else:
                # Default to subtle enhancement if no specific effect detected
                saturation_adjustment = 1.2
                contrast_adjustment = 1.1
                print(f"✨ Applying general video enhancement")
            
            final_output = f"{base_name}_edited.mp4"
            
            if i == 0:
                # First operation - need to trim the specific segment first if timestamps are available
                start_seconds = timestamps[0]
                duration_seconds = timestamps[1] - timestamps[0]
                
                start_time = f"{int(start_seconds//3600):02d}:{int((start_seconds%3600)//60):02d}:{int(start_seconds%60):02d}"
                duration_time = f"{int(duration_seconds//3600):02d}:{int((duration_seconds%3600)//60):02d}:{int(duration_seconds%60):02d}"
                
                print(f"Applying effects from {start_time} for duration {duration_time}")
                
                # Create temporary trimmed file first
                temp_trimmed = f"{base_name}_temp_effects_{int(start_seconds)}s_to_{int(timestamps[1])}s.mp4"
                temp_effects_applied = f"{base_name}_temp_with_effects.mp4"
                
                # Step 1: Trim the segment
                print("Step 1: Trimming segment...")
                trim_result = utils.trim_video(
                    input_path=current_video_path,
                    output_path=temp_trimmed,
                    start_time=start_time,
                    duration=duration_time,
                    precise=True
                )
                
                if not trim_result["success"]:
                    print(f"❌ Error trimming segment: {trim_result['error']}")
                    continue
                
                # Step 2: Apply effects to the trimmed segment
                print("Step 2: Applying video effects...")
                effects_result = utils.apply_video_effects(
                    input_path=temp_trimmed,
                    output_path=temp_effects_applied,
                    blur=int(blur_amount),
                    brightness=brightness_adjustment,
                    contrast=contrast_adjustment,
                    saturation=saturation_adjustment,
                    artistic_filter=artistic_filter
                )
                
                if not effects_result["success"]:
                    print(f"❌ Error applying effects: {effects_result['error']}")
                    # Clean up temporary files
                    if os.path.exists(temp_trimmed):
                        os.remove(temp_trimmed)
                    continue
                
                # Step 3: Replace the segment back into the original video
                print("Step 3: Replacing segment in original video...")
                
                # Get original video duration for context
                info_result = utils.get_media_info(current_video_path)
                if info_result["success"]:
                    total_duration_seconds = float(info_result["info"]["format"]["duration"])
                    
                    # Create parts: before effect, effect, after effect
                    temp_before = f"{base_name}_temp_before.mp4"
                    temp_after = f"{base_name}_temp_after.mp4"
                    temp_concat = "temp_effects_concat.txt"
                    
                    parts_to_concat = []
                    
                    # Part 1: Before the effect (if start > 0)
                    if start_seconds > 1:  # Only if there's more than 1 second before
                        before_duration = f"{int(start_seconds//3600):02d}:{int((start_seconds%3600)//60):02d}:{int(start_seconds%60):02d}"
                        
                        print(f"Creating before segment: start=00:00:00, duration={before_duration}")
                        
                        before_result = utils.trim_video(
                            input_path=current_video_path,
                            output_path=temp_before,
                            start_time="00:00:00",
                            duration=before_duration,
                            precise=True
                        )
                        if before_result["success"]:
                            parts_to_concat.append(temp_before)
                            print(f"✅ Before segment created successfully")
                        else:
                            print(f"❌ Error creating before segment: {before_result['error']}")
                    else:
                        print("No before segment needed (effect starts at beginning)")
                    
                    # Part 2: The effect segment
                    parts_to_concat.append(temp_effects_applied)
                    
                    # Part 3: After the effect (if end < total duration)
                    end_seconds = timestamps[1]
                    if end_seconds < total_duration_seconds - 1:  # Leave 1 second buffer
                        after_start_time = f"{int(end_seconds//3600):02d}:{int((end_seconds%3600)//60):02d}:{int(end_seconds%60):02d}"
                        remaining_duration = total_duration_seconds - end_seconds
                        after_duration_time = f"{int(remaining_duration//3600):02d}:{int((remaining_duration%3600)//60):02d}:{int(remaining_duration%60):02d}"
                        
                        print(f"Creating after segment: start={after_start_time}, duration={after_duration_time}")
                        
                        after_result = utils.trim_video(
                            input_path=current_video_path,
                            output_path=temp_after,
                            start_time=after_start_time,
                            duration=after_duration_time,
                            precise=True
                        )
                        if after_result["success"]:
                            parts_to_concat.append(temp_after)
                            print(f"✅ After segment created successfully")
                        else:
                            print(f"❌ Error creating after segment: {after_result['error']}")
                    else:
                        print("No after segment needed (effect goes to end of video)")
                    
                    # Debug: Print parts to concatenate
                    print(f"🔧 Parts to concatenate: {len(parts_to_concat)} files")
                    for j, part in enumerate(parts_to_concat):
                        if os.path.exists(part):
                            part_size = os.path.getsize(part)
                            print(f"   Part {j+1}: {part} ({part_size / (1024*1024):.2f} MB)")
                        else:
                            print(f"   Part {j+1}: {part} (FILE MISSING!)")
                    
                    # Concatenate all parts
                    if len(parts_to_concat) > 1:
                        with open(temp_concat, 'w') as f:
                            for part in parts_to_concat:
                                f.write(f"file '{os.path.abspath(part)}'\n")
                        
                        print(f"📝 Concat file contents:")
                        with open(temp_concat, 'r') as f:
                            print(f.read())
                        
                        concat_command = [
                            'ffmpeg', '-f', 'concat', '-safe', '0',
                            '-i', temp_concat,
                            '-c', 'copy',
                            '-avoid_negative_ts', 'make_zero',
                            '-fflags', '+genpts',
                            '-y', final_output
                        ]
                        
                        print(f"🔧 Running concat command: {' '.join(concat_command)}")
                        
                        import subprocess
                        concat_result = subprocess.run(concat_command, capture_output=True, text=True)
                        
                        if concat_result.returncode == 0:
                            print(f"✅ Video effects applied successfully!")
                            print(f"📁 Output file: {final_output}")
                            print(f"📂 Full path: {os.path.abspath(final_output)}")
                            
                            # Check if file exists and get size
                            if os.path.exists(final_output):
                                file_size = os.path.getsize(final_output)
                                print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                            
                            # Update current video path for next operation
                            current_video_path = final_output
                            # Add to output_files if this is the first successful operation or if output_files is empty
                            if i == 0 or len(output_files) == 0:
                                output_files.append(final_output)
                        else:
                            print(f"❌ Error concatenating video parts:")
                            print(f"   Return code: {concat_result.returncode}")
                            print(f"   STDERR: {concat_result.stderr}")
                            print(f"   STDOUT: {concat_result.stdout}")
                    else:
                        # Only one part - just copy the effects applied segment
                        import shutil
                        shutil.copy2(temp_effects_applied, final_output)
                        
                        print(f"✅ Video effects applied successfully!")
                        print(f"📁 Output file: {final_output}")
                        print(f"📂 Full path: {os.path.abspath(final_output)}")
                        
                        # Update current video path for next operation
                        current_video_path = final_output
                        if i == 0 or len(output_files) == 0:
                            output_files.append(final_output)
                    
                    # Clean up temporary files
                    for temp_file in [temp_trimmed, temp_effects_applied, temp_before, temp_after, temp_concat]:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                
                else:
                    print(f"❌ Could not get video info for concatenation")
                    # Clean up temporary files
                    for temp_file in [temp_trimmed, temp_effects_applied]:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
            
            else:
                # Subsequent operation - apply effects to entire current video
                print("Applying effects to entire current video...")
                
                effects_result = utils.apply_video_effects(
                    input_path=current_video_path,
                    output_path=final_output,
                    blur=int(blur_amount),
                    brightness=brightness_adjustment,
                    contrast=contrast_adjustment,
                    saturation=saturation_adjustment,
                    artistic_filter=artistic_filter
                )
                
                if effects_result["success"]:
                    print(f"✅ Video effects applied successfully!")
                    print(f"📁 Output file: {final_output}")
                    print(f"📂 Full path: {os.path.abspath(final_output)}")
                    
                    # Check if file exists and get size
                    if os.path.exists(final_output):
                        file_size = os.path.getsize(final_output)
                        print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
                    
                    # Update current video path for next operation
                    current_video_path = final_output
                    # Add to output_files if this is the first successful operation or if output_files is empty
                    if i == 0 or len(output_files) == 0:
                        output_files.append(final_output)
                else:
                    print(f"❌ Error applying effects: {effects_result['error']}")
                    print(f"FFmpeg output: {effects_result['output']}")
                    print(f"FFmpeg error: {effects_result['error']}")
        
        else:
            print(f"⚠️  Unsupported command: '{command}'")
            print("Supported commands: trim, clip trimming, dynamic zoom, zoom, sound effect, boom effect, splice, cut out, add subtitles, video effects")
    
    return output_files  # Return list of output files

# Run the editing process and get output files
instances = intent_extraction()
commands = timestamp_extraction(instances, vid_path)
output_files = run_edits(commands, original_instances=instances)

# Display summary of all output files
if output_files:
    print("\n" + "="*50)
    print("🎬 EDITING COMPLETE!")
    print("="*50)
    print("📁 Generated files:")
    for i, file_path in enumerate(output_files, 1):
        print(f"  {i}. {file_path}")
        print(f"     Full path: {os.path.abspath(file_path)}")
        
        # Check if file exists and get info
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"     Size: {file_size / (1024*1024):.2f} MB")
        else:
            print("     ⚠️  File not found!")
        print()
    
    print("💡 You can now:")
    print("   - Open the files in any video player")
    print("   - Use them in other applications")
    print("   - Further edit them with the utils functions")
    
else:
    print("\n❌ No output files were generated. Check the error messages above.")