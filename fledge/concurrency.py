"""Concurrency limiter — caps the number of jobs running simultaneously."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ConcurrencyPolicy:
    max_workers: int = 4

    @classmethod
    def from_dict(cls, data: dict) -> "ConcurrencyPolicy":
        return cls(
            max_workers=int(data.get("max_workers", 4)),
        )


class ConcurrencyLimiter:
    """Tracks how many jobs are currently executing and enforces a cap."""

    def __init__(self, policy: ConcurrencyPolicy) -> None:
        self._policy = policy
        self._lock = threading.Lock()
        self._active: Dict[str, int] = {}  # job_name -> active count
        self._semaphore = threading.Semaphore(policy.max_workers)

    @property
    def max_workers(self) -> int:
        return self._policy.max_workers

    @property
    def active_count(self) -> int:
        with self._lock:
            return sum(self._active.values())

    def acquire(self, job_name: str) -> bool:
        """Try to acquire a slot.  Returns True if acquired, False if at capacity."""
        acquired = self._semaphore.acquire(blocking=False)
        if acquired:
            with self._lock:
                self._active[job_name] = self._active.get(job_name, 0) + 1
        return acquired

    def release(self, job_name: str) -> None:
        """Release a previously acquired slot."""
        with self._lock:
            count = self._active.get(job_name, 0)
            if count <= 1:
                self._active.pop(job_name, None)
            else:
                self._active[job_name] = count - 1
        self._semaphore.release()

    def is_at_capacity(self) -> bool:
        return self.active_count >= self._policy.max_workers

    def active_jobs(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._active)
