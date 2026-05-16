"""Exponential backoff policy for job retry delays."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class BackoffPolicy:
    """Controls how retry delays grow between attempts."""

    base_delay: float = 1.0      # seconds before first retry
    multiplier: float = 2.0      # factor applied each retry
    max_delay: float = 60.0      # ceiling on any single delay
    jitter: float = 0.0          # fractional random jitter (0.0 – 1.0)

    @classmethod
    def from_dict(cls, data: dict) -> "BackoffPolicy":
        """Build a BackoffPolicy from a raw config mapping."""
        def _clamp(value: float, lo: float, hi: float) -> float:
            return max(lo, min(hi, value))

        return cls(
            base_delay=_clamp(float(data.get("base_delay", 1.0)), 0.0, 3600.0),
            multiplier=_clamp(float(data.get("multiplier", 2.0)), 1.0, 100.0),
            max_delay=_clamp(float(data.get("max_delay", 60.0)), 0.0, 86400.0),
            jitter=_clamp(float(data.get("jitter", 0.0)), 0.0, 1.0),
        )

    @property
    def enabled(self) -> bool:
        """Backoff is meaningful only when base_delay > 0."""
        return self.base_delay > 0.0

    def delays(self, max_attempts: int) -> Iterator[float]:
        """Yield one delay (seconds) per retry attempt.

        The number of yielded values equals *max_attempts* so callers can
        zip it with a range without worrying about off-by-one errors.
        """
        import random

        for attempt in range(max_attempts):
            raw = self.base_delay * math.pow(self.multiplier, attempt)
            capped = min(raw, self.max_delay)
            if self.jitter:
                capped += random.uniform(0.0, capped * self.jitter)
            yield capped
