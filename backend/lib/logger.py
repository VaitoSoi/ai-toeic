import logging

from .env import LOGGING_LEVEL

logger = logging.getLogger("uvicorn")
logger.setLevel(LOGGING_LEVEL)
