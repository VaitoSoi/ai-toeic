from fastapi import APIRouter

from lib.db import Statistics, statistics

route = APIRouter(prefix="/statistics", tags=["statistics"])


@route.get("/", response_model=Statistics, operation_id="get_statistics")
async def api_statistics():
    return await statistics()
