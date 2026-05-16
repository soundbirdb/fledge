"""Job dependency tracking — ensures a job only runs after its declared dependencies have succeeded."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class DependencyPolicy:
    requires: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "DependencyPolicy":
        raw = data.get("requires", [])
        if isinstance(raw, str):
            raw = [r.strip() for r in raw.split(",") if r.strip()]
        return cls(requires=list(raw))

    @property
    def enabled(self) -> bool:
        return bool(self.requires)


class DependencyTracker:
    """Tracks which jobs have completed successfully in the current tick."""

    def __init__(self) -> None:
        self._succeeded: Set[str] = set()
        self._failed: Set[str] = set()

    def record_success(self, job_name: str) -> None:
        self._succeeded.add(job_name)
        self._failed.discard(job_name)

    def record_failure(self, job_name: str) -> None:
        self._failed.add(job_name)
        self._succeeded.discard(job_name)

    def reset(self) -> None:
        """Clear state between daemon ticks."""
        self._succeeded.clear()
        self._failed.clear()

    def dependencies_met(self, policy: DependencyPolicy) -> bool:
        """Return True when every required job has succeeded this tick."""
        if not policy.enabled:
            return True
        return all(dep in self._succeeded for dep in policy.requires)

    def blocked_by(self, policy: DependencyPolicy) -> List[str]:
        """Return names of required jobs that have not yet succeeded."""
        return [dep for dep in policy.requires if dep not in self._succeeded]

    @property
    def succeeded(self) -> Set[str]:
        return frozenset(self._succeeded)  # type: ignore[return-value]

    @property
    def failed(self) -> Set[str]:
        return frozenset(self._failed)  # type: ignore[return-value]
