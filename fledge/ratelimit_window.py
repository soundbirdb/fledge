"""Sliding-window rate limiter that caps job executions within a rolling time span."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Deque


@dataclass
class SlidingWindowPolicy:
    max_calls: int = 0          # 0 → disabled
    window_seconds: float = 60.0

    @classmethod
    def from_dict(cls, data: dict) -> "SlidingWindowPolicy":
        raw = data.get("sliding_window", {})
        if not isinstance(raw, dict):
            return cls()
        max_calls = int(raw.get("max_calls", 0))
        window = float(raw.get("window_seconds", 60.0))
        if window <= 0:
            window = 60.0
        if max_calls < 0:
            max_calls = 0
        return cls(max_calls=max_calls, window_seconds=window)

    @property
    def enabled(self) -> bool:
        return self.max_calls > 0


class SlidingWindowLimiter:
    """Per-job sliding-window rate limiter."""

    def __init__(self) -> None:
        self._windows: Dict[str, Deque[float]] = {}

    def _get_window(self, job_name: str) -> Deque[float]:
        if job_name not in self._windows:
            self._windows[job_name] = deque()
        return self._windows[job_name]

    def is_allowed(self, job_name: str, policy: SlidingWindowPolicy) -> bool:
        """Return True if the job may execute under the policy."""
        if not policy.enabled:
            return True
        now = time.monotonic()
        window = self._get_window(job_name)
        cutoff = now - policy.window_seconds
        while window and window[0] < cutoff:
            window.popleft()
        return len(window) < policy.max_calls

    def record(self, job_name: str) -> None:
        """Record that *job_name* executed right now."""
        self._get_window(job_name).append(time.monotonic())

    def remaining(self, job_name: str, policy: SlidingWindowPolicy) -> int:
        """Return how many calls are still allowed in the current window."""
        if not policy.enabled:
            return -1
        now = time.monotonic()
        window = self._get_window(job_name)
        cutoff = now - policy.window_seconds
        active = sum(1 for t in window if t >= cutoff)
        return max(0, policy.max_calls - active)
