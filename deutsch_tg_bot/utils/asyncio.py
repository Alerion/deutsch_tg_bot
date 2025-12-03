import asyncio
from functools import wraps
from typing import Callable, Coroutine


def async_to_sync[R, **P](func: Callable[P, Coroutine[None, None, R]]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return asyncio.run(func(*args, **kwargs))

    return wrapper
