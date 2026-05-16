"""Retry policy configuration and execution logic for fledge jobs."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger("fledge")


@dataclass
class RetryPolicy:
    """Defines how a job should be retried on failure."""

    max_attempts: int = 1
    delay_seconds: float = 5.0
    backoff_factor: float = 1.0

    @classmethod
    def from_dict(cls, data: dict) -> "RetryPolicy":
        return cls(
            max_attempts=int(data.get("max_attempts", 1)),
            delay_seconds=float(data.get("delay_seconds", 5.0)),
            backoff_factor=float(data.get("backoff_factor", 1.0)),
        )

    def delays(self):
        """Yield successive delay durations for each retry attempt."""
        delay = self.delay_seconds
        for _ in range(self.max_attempts - 1):
            yield delay
            delay *= self.backoff_factor


def run_with_retry(
    fn: Callable[[], bool],
    policy: RetryPolicy,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> tuple[bool, int]:
    """Run *fn* up to policy.max_attempts times.

    Returns (success, attempts_used).
    Uses *sleep_fn* for waiting between retries (defaults to time.sleep).
    """
    if sleep_fn is None:
        sleep_fn = time.sleep

    delays = list(policy.delays())
    for attempt in range(1, policy.max_attempts + 1):
        success = fn()
        if success:
            return True, attempt
        if attempt < policy.max_attempts:
            wait = delays[attempt - 1]
            logger.debug(
                "Retry attempt %d/%d failed; waiting %.1fs before next attempt.",
                attempt,
                policy.max_attempts,
                wait,
            )
            sleep_fn(wait)

    return False, policy.max_attempts
