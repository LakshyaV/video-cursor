# The purpose of this file is to refine user prompt and check whether it is vague or not.

from xmlrpc import client
import cohere
import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem
from twelvelabs.tasks import TasksRetrieveResponse
from glob import glob
from dotenv import load_dotenv
import time
load_dotenv()

def upload_video():
    client = TwelveLabs(api_key=os.getenv("api_key_1"))
    index = client.indexes.create(
        index_name="pls im gaFIEIcsFVNEyvu",
        models=[
            IndexesCreateRequestModelsItem(
                model_name="pegasus1.2", model_options=["visual", "audio"]
            ),
            IndexesCreateRequestModelsItem(
                model_name="marengo2.7",
                model_options=["visual", "audio"],
            )
        ]
    )
    video_files = glob(r"C:/Users/prabh/Desktop/video-cursor/output_converted1.mp4")
    for video_file in video_files:
        print(f"Uploading {video_file}")
        with open(video_file, "rb") as f:
            task = client.tasks.create(index_id=index.id, video_file=f)
        print("Uploading video...")
        time.sleep(90)
        return index,video_file

def vague_or_specific():
    load_dotenv()
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("Error: COHERE_API_KEY not found in .env file.")
        return
    co = cohere.ClientV2(api_key)
    user_input = input("Describe your video edit request: ")
    prompt = (
        f"The following is a user request for a video edit: '{user_input}'. "
        "Is this a vague ask or a specific ask for a video edit? "
        "Reply with either 'vague' or 'specific'."
    )
    response = co.chat(
        model="command-a-03-2025",
        messages=[{"role": "user", "content": prompt}]
    )

    if hasattr(response, 'text'):
        print(response.text.strip())
    elif hasattr(response, 'message') and hasattr(response.message, 'content'):
        for item in response.message.content:
            if hasattr(item, 'text'):
                print(item.text.strip())
    else:
        print(response)