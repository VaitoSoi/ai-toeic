from fastapi import APIRouter

from lib.db import Statistics, statistics

route = APIRouter(
    prefix="/statistics",
    tags=['statistics']
)

@route.get("/", response_model=Statistics)
async def api_average_score():
    return await statistics()
