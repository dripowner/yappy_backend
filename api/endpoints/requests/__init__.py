import uuid
import arq.jobs
from fastapi import Depends, APIRouter, HTTPException, Response, status,  UploadFile, File
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from datetime import date, datetime
from api.db_model import Coords, RequestToTransaction, ShedulePathRequest, User, TransactionHistory, UsersToRequest, get_session, MLModel
from api.endpoints.auth.FastAPI_users import current_active_user
from api.endpoints.auth.manuspect_users import auth_manuspect_user
from api.endpoints.predict.utils import validate_model_name
from sqlalchemy.ext.asyncio import AsyncSession
from api.Asyncrq import asyncrq
from fastapi_limiter.depends import RateLimiter
from arq.jobs import Job
import arq
# from api.s3 import s3

router = APIRouter(
    dependencies=[Depends(RateLimiter(times=15, seconds=5))],
)


# TODO
# @router.get(
#     "/",
#     status_code=status.HTTP_200_OK,
# )
# async def get_doc(
#     request: str,
#     target_class: str,
#     user: User = Depends(current_active_user),
#     session: AsyncSession = Depends(get_session),

# ):
#     results = await session.execute(select(MLModel))
#     models = results.scalars().all()
#     return [model.__dict__ for model in models]


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_200_OK
)
async def delete_request(
    auth_token: str,
    request_id: str,
    session: AsyncSession = Depends(get_session)
):
    user: User = await auth_manuspect_user(auth_token, session)
    # Fetch the request to ensure it exists and is associated with the user
    result = await session.execute(
        select(ShedulePathRequest)
        .join(UsersToRequest, UsersToRequest.requests_id == ShedulePathRequest.id)
        .filter(
            UsersToRequest.user_id == user.id,
            ShedulePathRequest.id == request_id,
            ShedulePathRequest.is_deleted == False
        )
    )
    request = result.scalars().first()

    # If the request is not found or already deleted, return a 404 error
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="request not found"
        )

    # Mark the request as deleted
    request.is_deleted = True
    session.add(request)
    await session.commit()

    return {"detail": "request deleted successfully"}


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def get_docs_info_by_user(
    auth_token: str,
    session: AsyncSession = Depends(get_session),
):
    user: User = await auth_manuspect_user(auth_token, session)
    # Создаем запрос с использованием JOIN между таблицами
    result = await session.execute(select(ShedulePathRequest).join(UsersToRequest, UsersToRequest.requests_id == ShedulePathRequest.id).filter(UsersToRequest.user_id == user.id, ShedulePathRequest.is_deleted == False))
    # Получение документов пользователя
    requests = result.scalars().all()
    return requests


@router.get(
    "/status/{req_id}",
    status_code=status.HTTP_200_OK,
)
async def get_request_info_by_user(
    req_id: str | None,
    auth_token: str,
    session: AsyncSession = Depends(get_session),
):
    user: User = await auth_manuspect_user(auth_token, session)

    # Создаем запрос с использованием JOIN между таблицами
    result = await session.execute(
        select(ShedulePathRequest)
        .join(UsersToRequest, UsersToRequest.requests_id == ShedulePathRequest.id)
        .join(RequestToTransaction, RequestToTransaction.requests_id == ShedulePathRequest.id)
        .filter(
            UsersToRequest.user_id == user.id,
            ShedulePathRequest.id == req_id,  # Добавляем условие по req_id
            ShedulePathRequest.is_deleted == False,
        )
        .limit(1)  # Ограничиваем количество результатов до одного
    )
    # Получаем один документ пользователя, если такой существует
    request = result.scalars().first()
    return request


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_description="The shedule path request has been successfully created. Please track the execution by job_id",
)
async def shedule_path_request(
    auth_token: str,
    start_coords_lon: float,
    start_coords_lat: float,
    end_coords_lon: float,
    end_coords_lat: float,
    max_vel: int,
    arc: str,
    name: str,
    date: datetime,
    # shedule_path_request: ShedulePath,
    session: AsyncSession = Depends(get_session),
):
    user: User = await auth_manuspect_user(auth_token, session)
    start_coords = Coords(
        id=uuid.uuid4(),
        lon_float=start_coords_lon, lat_float=start_coords_lat)
    session.add(start_coords)

    end_coords = Coords(
        id=uuid.uuid4(),
        lon_float=end_coords_lon, lat_float=end_coords_lat)
    session.add(end_coords)

    await session.commit()

    # await s3.upload_file(file=request.file, filename=str(req_id))
    new_requests = ShedulePathRequest(
        id=uuid.uuid4(), start_coords_id=start_coords.id, end_coords_id=end_coords.id, max_vel=max_vel, arc=arc, name=name, date=date)
    session.add(new_requests)

    new_users_to_requests = UsersToRequest(
        user_id=user.id, requests_id=new_requests.id)
    session.add(new_users_to_requests)

    await session.commit()

    transaction = TransactionHistory(
        job_id=uuid.uuid4(),
        user_id=user.id,
        req_id=new_requests.id,
        amount=0,
        model_id=None,
    )

    session.add(transaction)

    await session.commit()

    new_requests_to_transaction = RequestToTransaction(
        requests_id=new_requests.id,
        transaction_history_id=transaction.job_id
    )
    session.add(new_requests_to_transaction)

    await session.commit()

    job = await asyncrq.pool.enqueue_job(
        function="analyze_requests",
        _job_id=str(transaction.job_id),
        req_id=str(new_requests.id),
    )

    info = await job.info()

    return {
        "job_id": str(job.job_id),
        "job_try": str(info.job_try),
        "req_id": str(new_requests.id),
        "enqueue_time": str(info.enqueue_time),
    }
