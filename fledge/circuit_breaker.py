"""Circuit breaker to temporarily disable jobs that repeatedly fail."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict


class BreakerState(Enum):
    CLOSED = "closed"      # normal operation
    OPEN = "open"          # blocking calls
    HALF_OPEN = "half_open"  # testing recovery


@dataclass
class CircuitBreakerPolicy:
    failure_threshold: int = 3
    recovery_timeout: float = 60.0  # seconds before moving to HALF_OPEN

    @classmethod
    def from_dict(cls, data: dict) -> "CircuitBreakerPolicy":
        return cls(
            failure_threshold=int(data.get("failure_threshold", 3)),
            recovery_timeout=float(data.get("recovery_timeout", 60.0)),
        )


@dataclass
class CircuitBreaker:
    policy: CircuitBreakerPolicy
    _state: BreakerState = field(default=BreakerState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _opened_at: float = field(default=0.0, init=False)

    @property
    def state(self) -> BreakerState:
        if self._state is BreakerState.OPEN:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self.policy.recovery_timeout:
                self._state = BreakerState.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        return self.state in (BreakerState.CLOSED, BreakerState.HALF_OPEN)

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = BreakerState.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self.policy.failure_threshold:
            self._state = BreakerState.OPEN
            self._opened_at = time.monotonic()


class CircuitBreakerRegistry:
    def __init__(self, policy: CircuitBreakerPolicy) -> None:
        self._policy = policy
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get(self, job_name: str) -> CircuitBreaker:
        if job_name not in self._breakers:
            self._breakers[job_name] = CircuitBreaker(policy=self._policy)
        return self._breakers[job_name]

    def states(self) -> Dict[str, str]:
        return {name: cb.state.value for name, cb in self._breakers.items()}
