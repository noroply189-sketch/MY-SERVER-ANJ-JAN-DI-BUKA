from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class TaskItem:
    name: str
    func: Callable[..., Awaitable[Any]]
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] | None = None


class TaskQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[TaskItem] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []

    async def enqueue(self, name: str, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> None:
        await self._queue.put(TaskItem(name=name, func=func, args=args, kwargs=kwargs))

    async def start(self, workers: int = 1) -> None:
        for _ in range(workers):
            self._workers.append(asyncio.create_task(self._worker_loop()))

    async def _worker_loop(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                await item.func(*item.args, **(item.kwargs or {}))
            finally:
                self._queue.task_done()

    async def wait_until_idle(self) -> None:
        await self._queue.join()

    async def shutdown(self) -> None:
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)


__all__ = ["TaskQueue", "TaskItem"]
