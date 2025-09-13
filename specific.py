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

vid_path = vague_or_nah.upload_video()

def intent_extraction():
    load_dotenv()
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("Error: COHERE_API_KEY not found in .env file.")
        return
    co = cohere.ClientV2(api_key)
    user_input = input("Describe your video edit request: ")
    prompt = ("Can you extract specific video edit commands from the following user request and list them in exactly the following format with no other additions: <explaincommand> AND <where in the video/audio it should be applied>, <command>, <where in the video/audio it should be applied> and so on. If there are no specific commands, reply with 'No specific commands found'. Here is the user request: " + f"'{user_input}'. ")
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


def timestamp_extraction(instances, vid_path):
    edit_demand_final = []
    client = TwelveLabs(api_key=os.getenv("api_key_1"))
    index = client.indexes.create(
        index_name="index_name",
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

    for i in range(len(instances)):
        query = instances[i][1]
        search_results = client.search.query(
            index_id=index.id,
            query_text=query,
            search_options=["visual", "audio"]
            )
        for clip in search_results:
            start={clip.start}
            end={clip.end}
            edit_demand_final.append([instances[i][0], start, end])

def run_edits(commands):
    for command in commands:
        