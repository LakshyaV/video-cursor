# The purpose of this file is to extract time stamps of specific instances from the video and run commands to edit those specific instances.

import cohere
import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem
from twelvelabs.tasks import TasksRetrieveResponse
from glob import glob
import vague_or_nah
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
    edit_demand_final = []
    client = TwelveLabs(api_key=os.getenv("api_key_1"))

    for i in range(len(instances)):
        query = "Find " + instances[i][1]
        print(query)
        search_results = client.search.query(
            index_id=index.id,
            query_text=query,
            search_options=["visual", "audio"]
        )
        for clip in search_results:
            print(f"video_id={clip.video_id} score={clip.score} start={clip.start} end={clip.end} confidence={clip.confidence}")

    print(edit_demand_final)

#def run_edits(commands):
 #   for command in commands:      

timestamp_extraction(intent_extraction(), vid_path)