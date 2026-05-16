"""Job priority ordering for the scheduler."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


# Lower numeric value = higher priority (like Unix nice levels).
_DEFAULT_PRIORITY = 50
_MIN_PRIORITY = 0
_MAX_PRIORITY = 100


@dataclass
class PriorityPolicy:
    """Defines the scheduling priority for a single job."""

    level: int = _DEFAULT_PRIORITY

    @classmethod
    def from_dict(cls, data: dict) -> "PriorityPolicy":
        raw = data.get("level", _DEFAULT_PRIORITY)
        try:
            level = int(raw)
        except (TypeError, ValueError):
            level = _DEFAULT_PRIORITY
        level = max(_MIN_PRIORITY, min(_MAX_PRIORITY, level))
        return cls(level=level)

    @property
    def enabled(self) -> bool:
        """Priority is always considered active; default is mid-range."""
        return True


@dataclass
class PriorityQueue:
    """Orders job names by their assigned priority levels."""

    _registry: dict = field(default_factory=dict)

    def register(self, job_name: str, policy: PriorityPolicy) -> None:
        """Register a job with its priority policy."""
        self._registry[job_name] = policy

    def sorted_jobs(self, job_names: List[str]) -> List[str]:
        """Return *job_names* sorted from highest to lowest priority.

        Jobs not in the registry are assigned the default priority.
        """
        return sorted(
            job_names,
            key=lambda name: self._registry.get(
                name, PriorityPolicy()
            ).level,
        )

    def level_for(self, job_name: str) -> int:
        """Return the numeric priority level for *job_name*."""
        return self._registry.get(job_name, PriorityPolicy()).level
