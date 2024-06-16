from api.typesense_db import TypesenseService
import json
from typing import Dict, Any

from sqlalchemy import select
from datetime import datetime, timedelta
from sqlalchemy.exc import NoResultFound
from .models.AudioDescription import AudioRecognition
from .models.Caption import Caption
# from api.s3 import s3
import traceback

caption_instance = Caption()
transcribe_instance = AudioRecognition()


async def analyze_requests(
    ctx: Dict[str, Any],
    url: str,
    description: str,
    **kwargs: Any,
):
    try:
        db = TypesenseService()

        video_intervals = caption_instance.shot_transit(url)
        # # Mock Data
        # video_intervals = [
        #     {
        #         "interval": "0:12:6",
        #         "caption": "Caption Text",
        #         "ocr": "ocr Text",
        #         "obj": "obj Text"
        #     }
        # ]

        output_item = process_video_results(url, description, video_intervals)
        db.update_videos(
            output_item, {'filter_by': f'url:={url} && description:={description}'})

        audio_intervals = transcribe_instance.audio_recognition(url)
        # # Mock Data
        # audio_intervals = [
        #     {
        #         "end_interval": "0:12:6",
        #         "text": "transcribation text"
        #     }
        # ]
        output_item = process_audio_results(url, description, audio_intervals)
        db.add_videos(output_item)
    except Exception as e:
        output_item = {
            "url": url,
            "description": description,
            "status": f'Error: {e}',
        }
        db.update_videos(
            output_item, {'filter_by': f'url:={url} && description:={description}'})


def process_video_results(url, description, video_intervals):
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
        end_time = datetime.strptime(item["interval"], "%H:%M:%S")
        output_item["content"] = "".join(
            [item["caption"], item["ocr"], item["obj"]])
        output_item["start_stop_interval"].append(
            str(start_time) + "-" + str(end_time))
    return output_item


def process_audio_results(url, description, audio_intervals):
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
        end_time = datetime.strptime(item["end_interval"], "%H:%M:%S")
        output_item["content"].append(item["text"])
        output_item["start_stop_interval"].append(
            str(start_time) + "-" + str(end_time))
    return output_item
