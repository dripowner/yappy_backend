import json
from typing import Dict, Any

from sqlalchemy import select
from worker.models.text_classification_hackaton import Model
from api.db_model import ShedulePathRequest, TransactionHistory, get_session, TransactionStatusEnum
from sqlalchemy.exc import NoResultFound
# from api.s3 import s3
import traceback

# model = Model()


async def analyze_requests(
    ctx: Dict[str, Any],
    req_id: str,
    **kwargs: Any,
):
    async for session in get_session():
        try:

            job_id = ctx.get("job_id", None)
            if not job_id:
                raise Exception("Something is wrong. job_id is None")

            transaction = await session.execute(
                select(TransactionHistory).filter_by(job_id=job_id)
            )
            transaction = transaction.scalar()

            req = await session.execute(
                select(ShedulePathRequest).filter_by(id=req_id)
            )
            req = req.scalar()

            # result = model.predict(data)

            departure_time = ""
            arrival_time = ""
            gantt_chart = ""

            # if not result:
            #     raise Exception(
            #         f"Something is wrong. Try again later: {result}")

            transaction.status = TransactionStatusEnum.SUCCESS

            json_data = json.dumps({"departure_time": departure_time,
                                   "arrival_time": arrival_time, "gantt_chart": gantt_chart})
            transaction.result = json_data
            await session.commit()
            return transaction.result
        except Exception as e:
            transaction.status = TransactionStatusEnum.FAILURE
            transaction.err_reason = str(e)
            await session.commit()
            traceback.print_exc()
            return json.dumps({"result": str(e)})
