import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lib.ai import init as ai_init
from lib.db import init as db_init
from lib.task import shutdown
from route import review_route, statics_route, submission_route, topic_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    ai_init()
    await db_init()
    yield
    await shutdown(10)


app = FastAPI(
    title="TOEIC Writing Platform",
    description="Powered by OpenRouter",
    lifespan=lifespan,
)

api_router = APIRouter()
api_router.include_router(review_route)
api_router.include_router(statics_route)
api_router.include_router(submission_route)
api_router.include_router(topic_route)

if not os.path.exists("data/image"):
    os.mkdir("data/image")
app.mount("/file", StaticFiles(directory="data/image"))

ENV = os.getenv("ENV", "DEV")
if ENV == "PROD":
    app.include_router(api_router, prefix="/api")

    if os.path.exists("static/assets"):
        app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        file_path = os.path.join("static", full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="not found")

        return FileResponse("static/index.html")

else:
    app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
