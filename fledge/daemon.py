"""Fledge daemon — orchestrates scheduler, runner, history, and notifier."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from fledge.config import FledgeConfig
from fledge.history import JobHistory
from fledge.logging_config import get_logger
from fledge.notifier import Notifier
from fledge.runner import JobRunner
from fledge.scheduler import Scheduler

logger = get_logger(__name__)


class Daemon:
    """Main daemon process."""

    def __init__(self, config: FledgeConfig) -> None:
        self._config = config
        self._scheduler = Scheduler(config.jobs)
        self._runner = JobRunner()
        self._notifier = Notifier(config.notifier)
        history_path: Optional[Path] = (
            Path(config.daemon.history_file) if config.daemon.history_file else None
        )
        self._history = JobHistory(history_path)
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Run the daemon loop until *stop()* is called."""
        logger.info("Fledge daemon starting")
        self._running = True
        try:
            while self._running:
                self._run_due_jobs()
                time.sleep(self._config.daemon.tick_seconds)
        except KeyboardInterrupt:
            logger.info("Interrupted — shutting down")
        finally:
            self._running = False
            logger.info("Fledge daemon stopped")

    def stop(self) -> None:
        """Signal the daemon loop to exit."""
        self._running = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_due_jobs(self) -> None:
        for job, schedule in self._scheduler.due_jobs():
            logger.info("Running job '%s'", job.name)
            result = self._runner.run(job)
            schedule.mark_ran()
            self._history.record(result)
            self._notifier.notify(result)
            if result.success:
                logger.info("Job '%s' completed in %.2fs", job.name, result.duration_seconds)
            else:
                logger.error(
                    "Job '%s' failed after %.2fs: %s",
                    job.name,
                    result.duration_seconds,
                    result.error,
                )
