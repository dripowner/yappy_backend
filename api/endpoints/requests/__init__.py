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
    #Search

    videos_collect: Collection = client.collections['videos']

    result_json = videos_collect.documents.search({
        'q': prompt,
        'query_by': description,
        },
        {
        'q': prompt,
        'query_by': content,
        }
    )

    for item in result_json:
        if item['status'] == 'done':
            return {
            "url": item['url'],
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
