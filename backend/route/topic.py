from typing import Literal

from fastapi import APIRouter

from lib.db import create_topic, delete_topic, get_topic, get_topics
from lib.response import exception_handler

route = APIRouter(
    prefix="/topic",
    tags=["topic"],
)


@route.get("s", description="Get all topics")
async def api_get_topics():
    return await get_topics()


@route.get("", description="Get a single topic")
@exception_handler
async def api_get_topic(id: str):
    return await get_topic(id)


@route.post("", description="Request a topic")
@exception_handler
async def api_create_topic(part: Literal["2"] | Literal["3"]):
    return await create_topic(part)

@route.delete("", description="Delete a topic")
@exception_handler
async def api_delete_topic(id: str):
    return await delete_topic(id)
