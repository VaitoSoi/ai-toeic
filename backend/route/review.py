from fastapi import APIRouter

from lib.db import get_review, get_review_of_submission, get_reviews, review
from lib.response import exception_handler

route = APIRouter(
    prefix="/review",
    tags=["review"],
)


@route.get("s", description="Get all reviews")
async def api_get_reviews():
    return await get_reviews()


@route.get("", description="Get a single review")
@exception_handler
async def api_get_review(id: str):
    return await get_review(id)

@route.get("/of", description="Get review of a Submission")
@exception_handler
async def api_get_review_of_submission(submission_id: str):
    return await get_review_of_submission(submission_id)

@route.post("", description="Request a review, return review id")
@exception_handler
async def api_review(submission_id: str):
    return (await review(submission_id))[1]
