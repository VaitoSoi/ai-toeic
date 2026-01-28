from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from lib.db import (
    SlicedTopic,
    create_topic,
    delete_topic,
    get_topic,
    get_topics,
    insert_topic,
)
from lib.response import exception_handler

route = APIRouter(
    prefix="/topic",
    tags=["topic"],
)

class InsertTopicBody(BaseModel):
    question: str

@route.get("s", description="Get all topics", response_model=list[SlicedTopic])
async def api_get_topics(all: bool = False):
    return await get_topics(all)


@route.get("", description="Get a single topic", response_model=SlicedTopic)
@exception_handler
async def api_get_topic(id: str):
    return await get_topic(id)


@route.post("", description="Request a topic", response_model=SlicedTopic)
@exception_handler
async def api_create_topic(part: Literal["1", "2", "3"], p1_count: int = 5):
    return await create_topic(part=part, p1_count=p1_count)

@route.post("/insert", description="Insert a topic", response_model=SlicedTopic)
@exception_handler
async def api_insert_topic(part: Literal["2", "3"], body: InsertTopicBody):
    return await insert_topic(part, body.question)

@route.delete("", description="Delete a topic")
@exception_handler
async def api_delete_topic(id: str):
    return await delete_topic(id)
