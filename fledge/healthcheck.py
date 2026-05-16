"""Simple health-check endpoint / status snapshot for the Fledge daemon."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from fledge.metrics import MetricsCollector


@dataclass
class JobHealth:
    """Health snapshot for a single job."""
    name: str
    total_runs: int
    failure_rate: float
    average_duration: float
    last_run_at: Optional[float]  # epoch seconds, or None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "total_runs": self.total_runs,
            "failure_rate": round(self.failure_rate, 4),
            "average_duration": round(self.average_duration, 4),
            "last_run_at": self.last_run_at,
        }


@dataclass
class HealthReport:
    """Aggregated health report for the daemon."""
    status: str  # "ok" | "degraded" | "unknown"
    uptime: float  # seconds since daemon started
    jobs: Dict[str, JobHealth] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "uptime": round(self.uptime, 2),
            "jobs": {name: jh.as_dict() for name, jh in self.jobs.items()},
        }


class HealthChecker:
    """Builds a :class:`HealthReport` from live daemon metrics."""

    # A job is considered *degraded* when its failure rate exceeds this value.
    DEGRADED_THRESHOLD: float = 0.5

    def __init__(self, metrics: MetricsCollector, start_time: Optional[float] = None) -> None:
        self._metrics = metrics
        self._start_time: float = start_time if start_time is not None else time.monotonic()

    def report(self) -> HealthReport:
        """Return a current :class:`HealthReport`."""
        uptime = time.monotonic() - self._start_time
        job_healths: Dict[str, JobHealth] = {}
        overall_degraded = False

        for name, jm in self._metrics.all().items():
            fr = jm.failure_rate()
            if fr > self.DEGRADED_THRESHOLD:
                overall_degraded = True
            job_healths[name] = JobHealth(
                name=name,
                total_runs=jm.total_runs,
                failure_rate=fr,
                average_duration=jm.average_duration(),
                last_run_at=jm.last_run_at,
            )

        status = "degraded" if overall_degraded else ("ok" if job_healths else "unknown")
        return HealthReport(status=status, uptime=uptime, jobs=job_healths)
