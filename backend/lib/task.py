import traceback
from asyncio import (
    AbstractEventLoop,
    Task,
    Timeout,
    create_task,
    gather,
    run_coroutine_threadsafe,
)
from typing import Any, Callable, Coroutine, TypeVar
from uuid import uuid4

tasks: dict[str, Task] = {}

T = TypeVar("T")


def add_task(
    coro: Coroutine[Any, Any, T],
    id: str = uuid4().__str__(),
    callback: Callable[[str, bool, T | None], Coroutine[Any, Any, Any]] | None = None,
    event_loop: AbstractEventLoop | None = None,
):
    task = create_task(coro, name=id)
    task.add_done_callback(_done_callback(id, callback, event_loop))
    tasks[id] = task
    return id


def _done_callback(
    id: str,
    callback: Callable[[str, bool, T | None], Coroutine[Any, Any, Any]] | None,
    event_loop: AbstractEventLoop | None,
):
    def _inner(task: Task[T]):
        if (task.exception()):
            print("".join(traceback.format_exception(task.exception())))
            if callback and event_loop:
                run_coroutine_threadsafe(coro=callback(id, False, None), loop=event_loop)
            return
        del tasks[id]
        if callback and event_loop:
            try:
                result = task.result()
                run_coroutine_threadsafe(
                    coro=callback(id, True, result), loop=event_loop
                )
            except Exception:
                run_coroutine_threadsafe(coro=callback(id, False, None), loop=event_loop)

    return _inner


def status(id: str):
    task = tasks[id]
    if not task:
        return None
    return task.done()


def cancel(id: str):
    task = tasks[id]
    if not task:
        return None
    return task.cancel()


async def shutdown(timeout: int | None = None):
    if timeout:
        try:
            async with Timeout(timeout):
                await gather(*list(tasks.values()), return_exceptions=True)
        except TimeoutError:
            _cancel_all_task()
    else:
        _cancel_all_task()


def _cancel_all_task():
    for _, task in tasks.items():
        task.cancel()
