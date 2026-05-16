"""Daemon orchestration: tick loop, scheduling, running, and metrics."""

from __future__ import annotations

import time
from typing import Optional

from fledge.config import DaemonConfig
from fledge.logging_config import get_logger
from fledge.metrics import MetricsCollector
from fledge.runner import JobRunner
from fledge.scheduler import Scheduler

logger = get_logger(__name__)


class Daemon:
    """Coordinates the scheduler, runner, and metrics collector."""

    def __init__(self, config: DaemonConfig) -> None:
        self._config = config
        self._scheduler = Scheduler(config.jobs)
        self._runner = JobRunner()
        self._metrics = MetricsCollector()
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def metrics(self) -> MetricsCollector:
        return self._metrics

    def start(self, tick: float = 1.0) -> None:
        logger.info("Daemon starting (tick=%.1fs)", tick)
        self._running = True
        try:
            while self._running:
                self._run_due_jobs()
                time.sleep(tick)
        except KeyboardInterrupt:
            logger.info("Interrupted — shutting down.")
        finally:
            self._running = False
            logger.info("Daemon stopped.")

    def stop(self) -> None:
        logger.info("Daemon stop requested.")
        self._running = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_due_jobs(self) -> None:
        due = self._scheduler.due_jobs()
        for schedule in due:
            job = schedule.job
            logger.info("Running job '%s'", job.name)
            t0 = time.monotonic()
            try:
                result = self._runner.run(job)
            except Exception as exc:  # noqa: BLE001
                duration = time.monotonic() - t0
                logger.exception(
                    "Unhandled exception while running job '%s' after %.3fs",
                    job.name,
                    duration,
                )
                self._metrics.record(job.name, success=False, duration=duration)
                schedule.mark_ran()
                continue
            duration = time.monotonic() - t0
            self._metrics.record(job.name, success=result.success, duration=duration)
            schedule.mark_ran()
            if result.success:
                logger.info(
                    "Job '%s' succeeded in %.3fs", job.name, duration
                )
            else:
                logger.warning(
                    "Job '%s' failed in %.3fs: %s",
                    job.name,
                    duration,
                    result.error,
                )
