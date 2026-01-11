import logging
from functools import wraps
from typing import Awaitable, Callable, TypeVar

from fastapi import HTTPException, status

from lib.env import LOGGING_LEVEL
from lib.exception import ReviewNotFound, SubmissionNotFound, TopicNotFound

logger = logging.getLogger("uvicorn")
logger.setLevel(LOGGING_LEVEL)

R = TypeVar("R")

def exception_handler(func: Callable[..., Awaitable[R]]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        
        except (TopicNotFound, SubmissionNotFound, ReviewNotFound) as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        
        except HTTPException as e:
            raise e

        except Exception as e:
            if isinstance(e, ValueError):
                logger.error("Failed to handle a value")
            elif isinstance(e, RuntimeError):
                logger.error("Failed while running a function")
            else:
                logger.error("Failed to handle an error")
            logger.debug("Debug info:")
            logger.debug("- Args:")
            for arg in args:
                logger.debug(f"  | {arg}")
            for arg in kwargs:
                logger.debug(f"  | {arg}: {kwargs[arg]}")
            logger.error(e, exc_info=True)

            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return wrapper
