"""Rate limiting for job execution — prevents a job from running more than
N times within a rolling time window."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


@dataclass
class RateLimitPolicy:
    max_calls: int = 0          # 0 means disabled
    window_seconds: int = 60

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimitPolicy":
        return cls(
            max_calls=int(data.get("max_calls", 0)),
            window_seconds=int(data.get("window_seconds", 60)),
        )

    @property
    def enabled(self) -> bool:
        return self.max_calls > 0


class RateLimiter:
    """Tracks call timestamps for a single job and decides whether it is
    allowed to run under the configured rate-limit policy."""

    def __init__(self, policy: RateLimitPolicy) -> None:
        self._policy = policy
        self._timestamps: Deque[float] = deque()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def is_allowed(self) -> bool:
        """Return True if the job may run right now."""
        if not self._policy.enabled:
            return True
        self._evict_old()
        return len(self._timestamps) < self._policy.max_calls

    def record_call(self) -> None:
        """Register that the job ran at this moment."""
        self._timestamps.append(time.monotonic())

    def remaining(self) -> int:
        """How many more calls are permitted in the current window."""
        if not self._policy.enabled:
            return -1  # unlimited
        self._evict_old()
        return max(0, self._policy.max_calls - len(self._timestamps))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict_old(self) -> None:
        cutoff = time.monotonic() - self._policy.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()


class RateLimiterRegistry:
    """Maintains one :class:`RateLimiter` per job name."""

    def __init__(self) -> None:
        self._limiters: dict[str, RateLimiter] = {}

    def get(self, job_name: str, policy: RateLimitPolicy) -> RateLimiter:
        if job_name not in self._limiters:
            self._limiters[job_name] = RateLimiter(policy)
        return self._limiters[job_name]
