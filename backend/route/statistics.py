from fastapi import APIRouter

from lib.db import statistics

route = APIRouter(
    prefix="/statistics",
    tags=['statistics']
)

@route.get("/")
async def api_average_score():
    return await statistics()
