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
# from api.s3 import s3

router = APIRouter(
    dependencies=[Depends(RateLimiter(times=15, seconds=5))],
)


@router.get(
    "/status/{req_id}",
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
    "/status/{req_id}",
    status_code=status.HTTP_200_OK,
)
async def get_request_info_by_url(
    url: str,
):

    results = ""
    return {
        "url": url,
        "results": results
    }


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_description="The shedule path request has been successfully created. Please track the execution by job_id",
)
async def shedule_path_request(
    url: str,
    description: str,
):

    job = await asyncrq.pool.enqueue_job(
        function="analyze_requests",
        url=url,
    )

    info = await job.info()

    return {
        "url": url,
        "enqueue_time": str(info.enqueue_time),
    }
