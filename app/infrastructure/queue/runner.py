"""
Background task runner.

What this is:
- A minimal in-process background runner for stage-2 async task prelude.

What it does:
- Submits task callables to a shared thread pool.
- Tracks futures by task_id for lightweight inspection.

Why this is done this way:
- Stage 2 needs a real async submission boundary before a full queue/worker
  platform exists.
- An in-process runner keeps the change small while preserving task state
  transitions such as queued and running.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock


class BackgroundTaskRunner:
    def __init__(self, *, max_workers: int) -> None:
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="agentops-task")
        self.lock = Lock()
        self.futures: dict[str, Future[None]] = {}

    def submit(self, task_id: str, fn) -> Future[None]:
        future = self.executor.submit(fn)
        with self.lock:
            self.futures[task_id] = future
        future.add_done_callback(lambda _: self._cleanup(task_id))
        return future

    def _cleanup(self, task_id: str) -> None:
        with self.lock:
            self.futures.pop(task_id, None)

    def is_active(self, task_id: str) -> bool:
        with self.lock:
            future = self.futures.get(task_id)
        return bool(future and not future.done())
