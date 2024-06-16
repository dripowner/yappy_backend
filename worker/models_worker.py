import json
from typing import Dict, Any

from sqlalchemy import select
from api.typesense_db import add_videos
from datetime import datetime, timedelta
from sqlalchemy.exc import NoResultFound
from models.AudioDescription import AudioRecognition
from models.Caption import Caption
# from api.s3 import s3
import traceback

caption_instance = Caption()
transcribe_instance = AudioRecognition()
from api.typesense_db import TypesenseService

async def analyze_requests(
    ctx: Dict[str, Any],
    url: str,
    description: str,
    **kwargs: Any,
):
    video_intervals = caption_instance.shot_transit(url)
    db = TypesenseService()

    start_time = datetime.min.time()
    end_time = datetime.min.time()
    output_item = {
            "url": url,  
            "description": description,
            "content": [],
            "status": "Done",
            "interval_type": "video",
            "start_stop_interval": []
        }
    for i, item in enumerate(video_intervals):
        if i > 0:
            start_time = end_time
        end_time = item["interval"]
        output_item["content"] = "".join([item["caption"], item["ocr"], item["obj"]])
        output_item["start_stop_interval"].append(start_time.strftime("%H:%M:%S") + "-" + end_time.strftime("%H:%M:%S"))
    db.update_videos(
        output_item, {'filter_by': f'url:={url} && description:={description}'})
    #db.add_videos(output_item)

    '''    video_data = {
        "url": url,
        "description": description,
        "content": ["some text", "some ocr text"],
        "interval_type": "video",
        "content": ["content segment 1", "content segment 2"],
        "start_stop_interval": ["00:00:00-00:02:00", "00:05:00-00:07:00"]
    }'''

    audio_intervals = transcribe_instance.audio_recognition(url)
    end_time = datetime.min.time()
    start_time = datetime.min.time()
    output_item = {
            "url": url,
            "description": description,
            "content": [],
            "status": "Done",
            "interval_type": "audio",
            "start_stop_interval": []
        }
    for i, item in enumerate(audio_intervals):
        if i > 0:
            start_time = end_time
        end_time = item["end_interval"]
        output_item["content"].append(item["text"])
        output_item["start_stop_interval"].append(start_time.strftime("%H:%M:%S") + "-" + end_time.strftime("%H:%M:%S"))
    db.add_videos(output_item)
    
