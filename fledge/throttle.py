"""Throttle: prevent a job from running more than once within a minimum interval."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ThrottlePolicy:
    """Per-job throttle configuration."""

    min_interval: float = 0.0  # seconds; 0 means no throttle

    @classmethod
    def from_dict(cls, data: dict) -> "ThrottlePolicy":
        return cls(
            min_interval=float(data.get("min_interval", 0.0)),
        )

    @property
    def enabled(self) -> bool:
        return self.min_interval > 0.0


class Throttle:
    """Tracks last-run timestamps and decides whether a job is throttled."""

    def __init__(self) -> None:
        self._last_run: Dict[str, float] = {}

    def is_throttled(self, job_name: str, policy: ThrottlePolicy) -> bool:
        """Return True if the job ran too recently and should be skipped."""
        if not policy.enabled:
            return False
        last = self._last_run.get(job_name)
        if last is None:
            return False
        return (time.monotonic() - last) < policy.min_interval

    def record(self, job_name: str) -> None:
        """Record that *job_name* just ran."""
        self._last_run[job_name] = time.monotonic()

    def last_run(self, job_name: str) -> Optional[float]:
        """Return the monotonic timestamp of the last run, or None."""
        return self._last_run.get(job_name)

    def reset(self, job_name: str) -> None:
        """Clear throttle state for a job (useful in tests)."""
        self._last_run.pop(job_name, None)
