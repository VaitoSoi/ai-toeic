from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from lib.db import (
    P1SubmitBody,
    SlicedSubmission,
    delete_submission,
    get_submission,
    get_submissions,
    p1_submit,
    p23_submit,
    # update_submission,
)
from lib.response import exception_handler

route = APIRouter(
    prefix="/submission",
    tags=["submission"],
)


class SubmitBody(BaseModel):
    submission: str


@route.get(
    "s",
    description="Get all submissions",
    response_model=list[SlicedSubmission],
    operation_id="get_submissions",
)
async def api_get_submissions():
    return await get_submissions()


@route.get(
    "",
    description="Get a single submission",
    response_model=SlicedSubmission,
    operation_id="get_submission",
)
@exception_handler
async def api_get_submission(id: str):
    return await get_submission(id)


@route.post(
    "",
    description="Submit a submission",
    response_model=SlicedSubmission,
    operation_id="submit_submission",
)
@exception_handler
async def api_submit(part: str, topic_id: str, body: SubmitBody | list[P1SubmitBody]):
    if part == "1":
        if not isinstance(body, list) or not isinstance(body[0], P1SubmitBody):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail={"message": "wrong body"}
            )
        return await p1_submit(topic_id=topic_id, submissions=body)
    elif part in ["2", "3"]:
        if not isinstance(body, SubmitBody):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail={"message": "wrong body"}
            )
        return await p23_submit(topic_id=topic_id, submitted_text=body.submission)
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail={"message": "wrong part"}
        )


# @route.put("", description="Update a submission")
# @exception_handler
# async def api_update_submission(id: str, body: SubmitBody):
#     return await update_submission(id=id, submitted_text=body.submission)


@route.delete(
    "",
    description="Delete a submission",
    operation_id="delete_submission",
)
@exception_handler
async def api_delete_submission(id: str):
    return await delete_submission(id)
