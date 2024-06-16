import json
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
# from api.s3 import s3
import traceback

from api.typesense_db import TypesenseService

# model = Model()


async def analyze_requests(
    ctx: Dict[str, Any],
    url: str,
    description: str,
    **kwargs: Any,
):
    db = TypesenseService()
    # result = model.predict(data)

    results = ""

    video_data = {
        "url": url,
        "description": description,
        "content": ["some text", "some ocr text"],
        "interval_type": "video",
        "content": ["content segment 1", "content segment 2"],
        "start_stop_interval": ["00:00:00-00:02:00", "00:05:00-00:07:00"]
    }
    results = db.update_videos(
        video_data, {'filter_by': f'url:={url} && description:={description}'})
    print(results)
    # if not result:
    #     raise Exception(
    #         f"Something is wrong. Try again later: {result}")

    json_data = json.dumps({"url": url,
                            "results": results})

    return json_data
