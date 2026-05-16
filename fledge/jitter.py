"""Jitter policy for spreading out job execution start times."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JitterPolicy:
    """Configuration for start-time jitter applied before a job runs."""

    max_seconds: float = 0.0
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "JitterPolicy":
        raw = data.get("max_seconds", 0.0)
        try:
            max_seconds = max(0.0, float(raw))
        except (TypeError, ValueError):
            max_seconds = 0.0

        enabled = bool(data.get("enabled", True))
        if max_seconds == 0.0:
            enabled = False

        return cls(max_seconds=max_seconds, enabled=enabled)

    @property
    def is_active(self) -> bool:
        return self.enabled and self.max_seconds > 0.0


class Jitter:
    """Applies random sleep jitter before a job is dispatched."""

    def __init__(self, policy: Optional[JitterPolicy] = None) -> None:
        self._policy = policy or JitterPolicy()

    def sleep(self) -> float:
        """Sleep for a random duration up to max_seconds.

        Returns the actual seconds slept (0.0 if jitter is inactive).
        """
        if not self._policy.is_active:
            return 0.0
        delay = random.uniform(0.0, self._policy.max_seconds)
        time.sleep(delay)
        return delay

    def sample(self) -> float:
        """Return a jitter value without sleeping (useful for testing/preview)."""
        if not self._policy.is_active:
            return 0.0
        return random.uniform(0.0, self._policy.max_seconds)
