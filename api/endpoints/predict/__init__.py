import uuid
import arq.jobs
from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy import select
from api.db_model import User, TransactionHistory, get_session, MLModel
from api.endpoints.auth.FastAPI_users import current_active_user
from api.endpoints.predict.utils import validate_model_name
from sqlalchemy.ext.asyncio import AsyncSession
from api.Asyncrq import asyncrq
from fastapi_limiter.depends import RateLimiter
from arq.jobs import Job
import arq

router = APIRouter(
    dependencies=[Depends(RateLimiter(times=15, seconds=5))],
)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def get_models_list(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    results = await session.execute(select(MLModel))
    models = results.scalars().all()
    return [model.__dict__ for model in models]


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
)
async def get_job_result(
    job_id: str,
    user: User = Depends(current_active_user),
):
    job = Job(job_id=job_id, redis=asyncrq.pool)
    res = await job.result(timeout=30)
    return res.tolist()[0]
