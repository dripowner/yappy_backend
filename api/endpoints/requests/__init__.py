import uuid
import arq.jobs
from fastapi import Depends, APIRouter, HTTPException, Response, status,  UploadFile, File
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from api.Asyncrq import asyncrq
from fastapi_limiter.depends import RateLimiter
from arq.jobs import Job
import arq

from api.typesense_db import TypesenseService
# from api.s3 import s3

router = APIRouter(
    dependencies=[Depends(RateLimiter(times=15, seconds=5))],
)


@router.get(
    "/search/{prompt}",
    status_code=status.HTTP_200_OK,
)
async def search_info_by_prompt(
    prompt: str,
):
    # TODO: Search

    url = ""
    return {
        "url": url,
        "details": ""
    }


@router.get(
    "/status/",
    status_code=status.HTTP_200_OK,
)
async def get_request_info_by_url(
    url: str,
):
    service = TypesenseService()
    results = service.search(url, 'videos', 'url')
    print(results)
    return results


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_description="The shedule path request has been successfully created. Please track the execution by job_id",
)
async def analyze_url_request(
    url: str,
    description: str,
):
    service = TypesenseService()
    video_data = {
        "url": url,
        "description": description,
        "content": [],
        "interval_type": "",
        "content": [],
        "start_stop_interval": [],
        "status": "In progress"
    }

    res = service.add_videos(video_data)
    print(res)

    job = await asyncrq.pool.enqueue_job(
        function="analyze_requests",
        url=url,
        description=description,
    )

    info = await job.info()

    return {
        "url": url,
        "enqueue_time": str(info.enqueue_time),
    }
