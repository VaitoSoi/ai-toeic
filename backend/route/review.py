from typing import Optional

from fastapi import APIRouter

from lib.db import (
    SlicedReview,
    delete_review,
    get_review,
    get_review_of_submission,
    get_reviews,
    review,
)
from lib.response import exception_handler

route = APIRouter(
    prefix="/review",
    tags=["review"],
)


@route.get(
    "s",
    description="Get all reviews",
    response_model=list[SlicedReview],
    operation_id="get_reviews",
)
async def api_get_reviews():
    return await get_reviews()


@route.get(
    "",
    description="Get a single review",
    response_model=SlicedReview,
    operation_id="get_review",
)
@exception_handler
async def api_get_review(id: str):
    return await get_review(id)


@route.get(
    "/of",
    description="Get review of a Submission",
    response_model=Optional[SlicedReview],
    operation_id="get_review_of_submission",
)
@exception_handler
async def api_get_review_of_submission(submission_id: str):
    return await get_review_of_submission(submission_id)


@route.post(
    "",
    description="Request a review, return review id",
    response_model=str,
    operation_id="request_review",
)
@exception_handler
async def api_review(submission_id: str):
    return (await review(submission_id))[1]


@route.delete(
    "",
    description="Delete a review",
    response_model=None,
    operation_id="delete_review",
)
async def api_delete_review(id: str):
    await delete_review(id)
    return {"message": "ok"}
