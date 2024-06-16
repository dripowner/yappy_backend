import json
from typing import Dict, Any

from sqlalchemy import select
from worker.models.text_classification_hackaton import Model
from sqlalchemy.exc import NoResultFound
# from api.s3 import s3
import traceback

# model = Model()


async def analyze_requests(
    ctx: Dict[str, Any],
    url: str,
    **kwargs: Any,
):
    req = req.scalar()
    # result = model.predict(data)

    results = ""

    # if not result:
    #     raise Exception(
    #         f"Something is wrong. Try again later: {result}")

    json_data = json.dumps({"url": url,
                            "results": results})

    return json_data
