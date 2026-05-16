"""Cooldown policy — prevents a job from running again too soon after success."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CooldownPolicy:
    seconds: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "CooldownPolicy":
        raw = data.get("cooldown", {})
        if not isinstance(raw, dict):
            return cls()
        seconds = float(raw.get("seconds", 0.0))
        if seconds < 0:
            seconds = 0.0
        return cls(seconds=seconds)

    @property
    def enabled(self) -> bool:
        return self.seconds > 0.0


class CooldownTracker:
    """Tracks the last successful completion time per job and enforces cooldown."""

    def __init__(self) -> None:
        self._last_success: Dict[str, float] = {}

    def record_success(self, job_name: str) -> None:
        """Record that *job_name* just completed successfully."""
        self._last_success[job_name] = time.monotonic()

    def is_cooling_down(self, job_name: str, policy: CooldownPolicy) -> bool:
        """Return True if the job must wait before running again."""
        if not policy.enabled:
            return False
        last = self._last_success.get(job_name)
        if last is None:
            return False
        return (time.monotonic() - last) < policy.seconds

    def remaining(self, job_name: str, policy: CooldownPolicy) -> float:
        """Return seconds remaining in the cooldown window (0.0 if not cooling)."""
        if not policy.enabled:
            return 0.0
        last = self._last_success.get(job_name)
        if last is None:
            return 0.0
        elapsed = time.monotonic() - last
        return max(0.0, policy.seconds - elapsed)
