"""Lightweight in-memory metrics collector for job run statistics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

from fledge.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class JobMetrics:
    """Accumulated statistics for a single job."""

    job_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    last_run_at: float | None = None
    last_duration_seconds: float | None = None
    durations: List[float] = field(default_factory=list)

    @property
    def failure_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.failed_runs / self.total_runs

    @property
    def average_duration(self) -> float | None:
        if not self.durations:
            return None
        return sum(self.durations) / len(self.durations)

    def record(self, success: bool, duration: float) -> None:
        self.total_runs += 1
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
        self.last_run_at = time.time()
        self.last_duration_seconds = duration
        self.durations.append(duration)


class MetricsCollector:
    """Collects and exposes per-job runtime metrics."""

    def __init__(self) -> None:
        self._metrics: Dict[str, JobMetrics] = {}

    def record(self, job_name: str, success: bool, duration: float) -> None:
        if job_name not in self._metrics:
            self._metrics[job_name] = JobMetrics(job_name=job_name)
        self._metrics[job_name].record(success, duration)
        logger.debug(
            "Metrics recorded for '%s': success=%s duration=%.3fs",
            job_name,
            success,
            duration,
        )

    def get(self, job_name: str) -> JobMetrics | None:
        return self._metrics.get(job_name)

    def all(self) -> Dict[str, JobMetrics]:
        return dict(self._metrics)

    def summary(self) -> List[dict]:
        rows = []
        for m in self._metrics.values():
            rows.append(
                {
                    "job": m.job_name,
                    "total": m.total_runs,
                    "ok": m.successful_runs,
                    "fail": m.failed_runs,
                    "failure_rate": round(m.failure_rate, 4),
                    "avg_duration": (
                        round(m.average_duration, 4)
                        if m.average_duration is not None
                        else None
                    ),
                }
            )
        return rows
