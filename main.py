from twelvelabs import TwelveLabs
from twelvelabs.indexes import IndexesCreateRequestModelsItem
from twelvelabs.tasks import TasksRetrieveResponse
from glob import glob
import os

# 1. Initialize the client
client = TwelveLabs(api_key=os.getenv("TWELVE_LABS_API_KEY"))

# # 2. Create an index
# index = client.indexes.create(
#     index_name="index_sigma",
#     models=[
#         IndexesCreateRequestModelsItem(
#             model_name="pegasus1.2", model_options=["visual", "audio"]
#         )
#     ]
# )
# print(f"Created index: id={index.id}")

# video_files = glob(r"C:/Users/prabh/Desktop/videocursor/output_fixed1.mp4")
# for video_file in video_files:
#     print(f"Uploading {video_file}")
#     with open(video_file, "rb") as f:
#         task = client.tasks.create(index_id=index.id, video_file=f)
#     print(f"Task id={task.id}")

#     print(f"Upload complete. The unique identifier of your video is {task.video_id}.")

# 5. Generate summaries, chapters, and highlights
res_summary = client.summarize(
    video_id="68c51a6b5e2e514f27fbf90a",
    type="summary",
    prompt="Generate a summary of this video, be specific, include timestamps every 5 seconds. iterate every 5 seconds and log the summary of what happenes when. make sure to not skip over anything ",
    # temperature= 0.2
)

print(f"Summary: {res_summary.summary}")