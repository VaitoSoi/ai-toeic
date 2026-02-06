import os

import dotenv

from .logger import logger

dotenv.load_dotenv()

DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///data/db.sqlite")

OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://ai.hackclub.com/proxy/v1/")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("no api key in env")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "google/gemini-3-flash-preview")
QUESTION_MODEL = os.getenv("QUESTION_MODEL", DEFAULT_MODEL)
REVIEW_MODEL = os.getenv("REVIEW_MODEL", DEFAULT_MODEL)
ARTIST_MODEL = os.getenv("ARTIST_MODEL", DEFAULT_MODEL) # Part 1 Image generator

USE_STREAM = os.getenv("USE_STREAM", "true").lower() in ["true", "t", "yes", "y", "1"]
try:
    STREAM_CHUNK = int(os.getenv("STREAM_CHUNK", "1000"))
    if STREAM_CHUNK <= 0:
        logger.error("STREAM_CHUNK is an invalid number, use default (1000)")
        STREAM_CHUNK = 1000

except TypeError:
    logger.error("STREAM_CHUNK is not a number, use default (1000)")
    STREAM_CHUNK = 1000

ENV = os.getenv("ENV", "DEV")
