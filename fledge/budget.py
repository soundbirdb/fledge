"""Execution budget: cap total job runs (across all jobs) per time window."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BudgetPolicy:
    max_runs: int = 0          # 0 = unlimited
    window_seconds: int = 3600  # rolling window length

    @classmethod
    def from_dict(cls, data: dict) -> "BudgetPolicy":
        raw = data.get("budget", {})
        max_runs = int(raw.get("max_runs", 0))
        window = int(raw.get("window_seconds", 3600))
        if max_runs < 0:
            max_runs = 0
        if window < 1:
            window = 1
        return cls(max_runs=max_runs, window_seconds=window)

    @property
    def enabled(self) -> bool:
        return self.max_runs > 0


class BudgetTracker:
    """Tracks run timestamps across all jobs and enforces a global budget."""

    def __init__(self, policy: BudgetPolicy) -> None:
        self._policy = policy
        self._timestamps: List[float] = []

    def _evict_old(self, now: float) -> None:
        cutoff = now - self._policy.window_seconds
        self._timestamps = [t for t in self._timestamps if t >= cutoff]

    def allowed(self) -> bool:
        """Return True if another run is permitted under the budget."""
        if not self._policy.enabled:
            return True
        now = time.monotonic()
        self._evict_old(now)
        return len(self._timestamps) < self._policy.max_runs

    def record(self) -> None:
        """Record that a run has just started."""
        self._timestamps.append(time.monotonic())

    @property
    def current_count(self) -> int:
        self._evict_old(time.monotonic())
        return len(self._timestamps)
