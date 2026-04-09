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
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="agentops-task")
        self.lock = Lock()
        self.futures: dict[str, Future[None]] = {}

    def submit(self, task_id: str, fn) -> Future[None]:
        future = self.executor.submit(fn)
        with self.lock:
            self.futures[task_id] = future
        future.add_done_callback(lambda _: self._cleanup(task_id))
        return future

    def cancel(self, task_id: str) -> bool:
        with self.lock:
            future = self.futures.get(task_id)
        if future is None:
            return False
        cancelled = future.cancel()
        if cancelled:
            self._cleanup(task_id)
        return cancelled

    def get_task_runtime_state(self, task_id: str) -> str:
        with self.lock:
            future = self.futures.get(task_id)
        if future is None:
            return "missing"
        if future.cancelled():
            return "cancelled"
        if future.running():
            return "running"
        if future.done():
            return "done"
        return "queued"

    def _cleanup(self, task_id: str) -> None:
        with self.lock:
            self.futures.pop(task_id, None)

    def is_active(self, task_id: str) -> bool:
        with self.lock:
            future = self.futures.get(task_id)
        return bool(future and not future.done())

    def list_active_task_ids(self) -> list[str]:
        with self.lock:
            return [task_id for task_id, future in self.futures.items() if not future.done()]

    def get_runtime_snapshot(self) -> dict[str, object]:
        active_task_ids = self.list_active_task_ids()
        return {
            "max_workers": self.max_workers,
            "active_task_count": len(active_task_ids),
            "active_task_ids": active_task_ids,
        }
