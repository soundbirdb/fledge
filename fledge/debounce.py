"""Debounce policy: suppress rapid re-execution of a job within a quiet period."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DebouncePolicy:
    """Configuration for debounce behaviour on a job."""

    seconds: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "DebouncePolicy":
        raw = data.get("debounce", {})
        if not isinstance(raw, dict):
            return cls()
        seconds = float(raw.get("seconds", 0.0))
        if seconds < 0.0:
            seconds = 0.0
        return cls(seconds=seconds)

    @property
    def enabled(self) -> bool:
        return self.seconds > 0.0


class DebounceTracker:
    """Tracks pending debounce state per job.

    A job is suppressed if it was *triggered* (marked pending) within the
    debounce window of the previous trigger.  Call ``trigger`` each time the
    scheduler considers a job due, and ``allow`` to check whether execution
    should proceed.
    """

    def __init__(self) -> None:
        self._last_trigger: Dict[str, float] = {}
        self._pending: Dict[str, float] = {}

    def trigger(self, job_name: str, policy: DebouncePolicy) -> None:
        """Record that *job_name* has been triggered now."""
        if not policy.enabled:
            return
        now = time.monotonic()
        self._pending[job_name] = now

    def allow(self, job_name: str, policy: DebouncePolicy) -> bool:
        """Return True if the job should run (quiet period has elapsed)."""
        if not policy.enabled:
            return True
        now = time.monotonic()
        triggered_at = self._pending.get(job_name)
        if triggered_at is None:
            return False
        elapsed = now - triggered_at
        if elapsed >= policy.seconds:
            # Quiet period elapsed — allow and clear pending state
            self._pending.pop(job_name, None)
            self._last_trigger[job_name] = now
            return True
        return False

    def reset(self, job_name: str) -> None:
        """Clear all debounce state for *job_name*."""
        self._pending.pop(job_name, None)
        self._last_trigger.pop(job_name, None)
