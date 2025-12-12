from asyncio import Timeout, sleep
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from lib.db import add_session

route = APIRouter(prefix="/session", tags=["session"])


@route.websocket("/")
async def session(websocket: WebSocket):
    await websocket.accept()
    start_time = datetime.now()

    try:
        while True:
            id = uuid4().__str__()
            
            await websocket.send_text(id)
            
            async with Timeout(5):
                response = await websocket.receive_text()
            
            if id != response:
                await websocket.close()
                break
            
            await sleep(1)
            
    except (WebSocketDisconnect, TimeoutError):
        ...

    end_time = datetime.now()
    await add_session(start_time, end_time)
