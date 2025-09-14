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
    co = cohere.Client(api_key)
    user_input = input("Describe your video edit request: ")
    prompt = ("You are given a very vague video edit request. Using the following detailed summary of the video, please categorize different edits that can be done to fulfill the user's request. Please categorize the video edit commands in exactly the following format with no other additions: <explaincommand> AND <where in the video/audio it should be applied>, <command>, <where in the video/audio it should be applied> and so on. If there are no specific commands, reply with 'No specific commands found'. Here is the user request: " + f"'{user_input}'. + Here is the detailed summary of the video: " + f"'{res_summary.summary}' " + "These are the different edit techniques that you can offer: clip trimming, transitions, audio effects, dynamic zoom, object face blur, face/object tracking, subtitles, video effects.")
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
    
    edit_demands = response.split(',')
    for i in range(len(edit_demands)):
        edit_demands[i] = edit_demands[i].split(' AND ')
    print(edit_demands)


def timestamp_extraction(instances):
    pass

def run_edits(timestamp, commands):
    pass