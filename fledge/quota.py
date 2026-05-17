"""Per-job run quota: cap the number of executions within a rolling time window."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


@dataclass
class QuotaPolicy:
    max_runs: int = 0          # 0 means unlimited
    window_seconds: int = 3600  # rolling window, default 1 hour

    @classmethod
    def from_dict(cls, data: dict) -> "QuotaPolicy":
        max_runs = int(data.get("max_runs", 0))
        window_seconds = int(data.get("window_seconds", 3600))
        if max_runs < 0:
            max_runs = 0
        if window_seconds < 1:
            window_seconds = 1
        return cls(max_runs=max_runs, window_seconds=window_seconds)

    @property
    def enabled(self) -> bool:
        return self.max_runs > 0


class QuotaTracker:
    """Tracks run timestamps for a single job and enforces the quota."""

    def __init__(self, policy: QuotaPolicy) -> None:
        self._policy = policy
        self._timestamps: Deque[float] = deque()

    def _evict_old(self, now: float) -> None:
        cutoff = now - self._policy.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def allowed(self, now: float | None = None) -> bool:
        """Return True if the job is permitted to run right now."""
        if not self._policy.enabled:
            return True
        if now is None:
            now = time.monotonic()
        self._evict_old(now)
        return len(self._timestamps) < self._policy.max_runs

    def record(self, now: float | None = None) -> None:
        """Record that the job ran at *now*."""
        if not self._policy.enabled:
            return
        if now is None:
            now = time.monotonic()
        self._evict_old(now)
        self._timestamps.append(now)

    @property
    def run_count(self) -> int:
        """Number of runs recorded inside the current window."""
        self._evict_old(time.monotonic())
        return len(self._timestamps)


class QuotaRegistry:
    """Holds one QuotaTracker per job name."""

    def __init__(self) -> None:
        self._trackers: dict[str, QuotaTracker] = {}

    def register(self, job_name: str, policy: QuotaPolicy) -> None:
        self._trackers[job_name] = QuotaTracker(policy)

    def get(self, job_name: str) -> QuotaTracker | None:
        return self._trackers.get(job_name)

    def allowed(self, job_name: str) -> bool:
        tracker = self._trackers.get(job_name)
        return tracker.allowed() if tracker is not None else True

    def record(self, job_name: str) -> None:
        tracker = self._trackers.get(job_name)
        if tracker is not None:
            tracker.record()
