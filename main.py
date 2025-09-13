from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem
from twelvelabs.tasks import TasksRetrieveResponse
from glob import glob
import os
from dotenv import load_dotenv
load_dotenv()

client = TwelveLabs(api_key=os.getenv("api_key_1"))

res_summary = client.summarize(
    video_id="68c51a6b5e2e514f27fbf90a",
    type="summary",
    prompt="Generate a summary of this video, be specific, include timestamps every 5 seconds. iterate every 5 seconds and log the summary of what happenes when. make sure to not skip over anything "
)

    print(f"Summary: {res_summary.summary}")

def search(query):
    search_results = client.search.query(
        index_id=index.id,
        query_text=query,
        search_options=["visual", "audio"]
        )
    for clip in search_results:  # iterate scores
        print(f"video_id={clip.video_id} score={clip.score} start={clip.start} end={clip.end} confidence={clip.confidence}")

search("where is the television")