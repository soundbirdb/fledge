"""Stagger policy: spread job start times across an interval to avoid thundering herd."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class StaggerPolicy:
    """Configuration for staggered job startup."""
    enabled: bool = False
    spread_seconds: float = 0.0  # total window to spread starts across

    @classmethod
    def from_dict(cls, data: dict) -> "StaggerPolicy":
        raw = data.get("stagger", {})
        if not raw:
            return cls()
        spread = float(raw.get("spread_seconds", 0.0))
        if spread < 0.0:
            spread = 0.0
        enabled = spread > 0.0
        return cls(enabled=enabled, spread_seconds=spread)


class StaggerTracker:
    """Assigns a deterministic per-job delay within a spread window.

    Jobs are assigned offsets based on their registration order so that
    start times are evenly distributed across ``spread_seconds``.
    """

    def __init__(self, policy: StaggerPolicy) -> None:
        self._policy = policy
        self._offsets: Dict[str, float] = {}
        self._count: int = 0
        self._start_time: float = time.monotonic()

    def register(self, job_name: str) -> None:
        """Register a job and assign it a stagger offset."""
        if job_name in self._offsets:
            return
        if not self._policy.enabled or self._policy.spread_seconds <= 0.0:
            self._offsets[job_name] = 0.0
        else:
            self._offsets[job_name] = self._count * (self._policy.spread_seconds / max(1, 1))
            # offset = index * (spread / n_jobs) computed lazily per registration
            self._offsets[job_name] = self._count * self._policy.spread_seconds
        self._count += 1

    def _recompute_offsets(self) -> None:
        """Redistribute offsets evenly across spread_seconds given current job count."""
        names = list(self._offsets.keys())
        n = len(names)
        if n == 0 or not self._policy.enabled:
            return
        step = self._policy.spread_seconds / n
        for i, name in enumerate(names):
            self._offsets[name] = i * step

    def offset_for(self, job_name: str) -> float:
        """Return the stagger offset in seconds for *job_name*."""
        self._recompute_offsets()
        return self._offsets.get(job_name, 0.0)

    def is_clear(self, job_name: str) -> bool:
        """Return True if the stagger delay for *job_name* has elapsed."""
        if not self._policy.enabled:
            return True
        offset = self.offset_for(job_name)
        elapsed = time.monotonic() - self._start_time
        return elapsed >= offset
