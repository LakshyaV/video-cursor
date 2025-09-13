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
    co = cohere.ClientV2(api_key)
    user_input = input("Describe your video edit request: ")
    prompt = (
    "Extract the specific video edit commands from the following user request. "
    "Output them **only** in this exact format: "
    "<command> AND <where in the video/audio it should be applied>, "
    "<command> AND <where in the video/audio it should be applied>, "
    "… (continue as needed). "
    "Do not include section titles, explanations, or any extra text—just the commands in the specified format. "
    "Here is the user request: '" + user_input + "'. "
    "Available edit techniques: clip trimming, transitions, audio effects, dynamic zoom, object face blur, "
    "face/object tracking, subtitles, video effects."
    )
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
        
        elif command.lower() in ["dynamic zoom", "zoom", "zoom effect", "zoom into", "zoom on"]:
            # Check if this is an object-based zoom request
            # Look for object names in the location part of the command
            location_text = ""
            if original_instances and i < len(original_instances):
                # Get the location text from the original instances
                location_text = original_instances[i][1] if len(original_instances[i]) > 1 else ""
            
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
                # Object-based zoom
                print(f"🎯 Detected object-based zoom request: '{target_object}'")
                
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
                
                # Use object-based zoom
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
        
        else:
            print(f"⚠️  Unsupported command: '{command}'")
            print("Supported commands: trim, clip trimming, dynamic zoom, zoom")
    
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
    
    # Ask user what they want to do with the output
    print("\n🎬 What would you like to do with the output files?")
    print("1. Open the first video file")
    print("2. Show file location in explorer")
    print("3. Copy to desktop")
    print("4. Do nothing")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1" and output_files:
            output_utils.open_video_file(output_files[0])
        elif choice == "2" and output_files:
            output_utils.open_file_location(output_files[0])
        elif choice == "3" and output_files:
            output_utils.copy_to_desktop(output_files[0])
        elif choice == "4":
            print("👍 Files are ready for you to use!")
        else:
            print("❌ Invalid choice or no output files available")
    except KeyboardInterrupt:
        print("\n👍 Files are ready for you to use!")
else:
    print("\n❌ No output files were generated. Check the error messages above.")