# The purpose of this file is to refine user prompt and check whether it is vague or not.

import cohere
import os
from dotenv import load_dotenv

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
    # Extract and print only the answer text
    if hasattr(response, 'text'):
        print(response.text.strip())
    elif hasattr(response, 'message') and hasattr(response.message, 'content'):
        for item in response.message.content:
            if hasattr(item, 'text'):
                print(item.text.strip())
    else:
        print(response)

if __name__ == "__main__":
    main()