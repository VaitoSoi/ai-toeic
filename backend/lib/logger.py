import logging
import os

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "info").upper()
logger = logging.getLogger("uvicorn")
logger.setLevel(LOGGING_LEVEL)
