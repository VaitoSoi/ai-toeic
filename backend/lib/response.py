from functools import wraps
from typing import Awaitable, Callable, TypeVar

from fastapi import HTTPException, status

from lib.exception import ReviewNotFound, SubmissionNotFound, TopicNotFound

R = TypeVar("R")


def exception_handler(func: Callable[..., Awaitable[R]]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (TopicNotFound, SubmissionNotFound, ReviewNotFound) as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise e

    return wrapper
