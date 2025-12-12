from fastapi import APIRouter
from pydantic import BaseModel

from lib.db import (
    delete_submission,
    get_submission,
    get_submissions,
    submit,
    update_submission,
)
from lib.response import exception_handler

route = APIRouter(
    prefix="/submission",
    tags=["submission"],
)


class SubmitBody(BaseModel):
    submission: str


@route.get("s", description="Get all submissions")
async def api_get_submissions():
    return await get_submissions()


@route.get("", description="Get a single submission")
@exception_handler
async def api_get_submission(id: str):
    return await get_submission(id)


@route.post("", description="Submit a submission")
@exception_handler
async def api_submit(topic_id: str, body: SubmitBody):
    return await submit(topic_id=topic_id, submitted_text=body.submission)

@route.put("", description="Update a submission")
@exception_handler
async def api_update_submission(id: str, body: SubmitBody):
    return await update_submission(id=id, submitted_text=body.submission)


@route.delete("", description="Delete a submission")
@exception_handler
async def api_delete_submission(id: str):
    return await delete_submission(id)
