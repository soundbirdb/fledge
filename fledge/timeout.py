"""Per-job execution timeout enforcement."""
from __future__ import annotations

import signal
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class TimeoutPolicy:
    seconds: int = 0  # 0 means disabled

    @classmethod
    def from_dict(cls, data: dict) -> "TimeoutPolicy":
        seconds = int(data.get("seconds", 0))
        return cls(seconds=max(0, seconds))

    @property
    def enabled(self) -> bool:
        return self.seconds > 0


class JobTimeoutError(Exception):
    """Raised when a job exceeds its allowed execution time."""


def _timeout_handler(signum: int, frame: Any) -> None:  # noqa: ARG001
    raise JobTimeoutError("Job exceeded timeout")


def run_with_timeout(fn: Callable[[], Any], policy: TimeoutPolicy) -> Any:
    """Execute *fn* and raise JobTimeoutError if it runs longer than policy.seconds.

    Uses SIGALRM, so this only works on Unix-like systems.  When the policy is
    disabled the function is called directly without any wrapping.
    """
    if not policy.enabled:
        return fn()

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(policy.seconds)
    try:
        return fn()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
