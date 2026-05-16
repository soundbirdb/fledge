"""Fledge daemon — orchestrates the scheduler, runner, and history."""

from __future__ import annotations

import time
from typing import Optional

from fledge.config import FledgeConfig
from fledge.history import HistoryEntry, JobHistory
from fledge.logging_config import get_logger
from fledge.runner import JobRunner
from fledge.scheduler import Scheduler

_DEFAULT_HISTORY_PATH = "fledge_history.jsonl"
_TICK_SECONDS = 10


class Daemon:
    def __init__(
        self,
        config: FledgeConfig,
        history_path: str = _DEFAULT_HISTORY_PATH,
    ) -> None:
        self._config = config
        self._logger = get_logger()
        self._scheduler = Scheduler(config.jobs)
        self._runner = JobRunner()
        self._history = JobHistory(history_path)
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._logger.info("Fledge daemon starting.")
        self._running = True
        try:
            while self._running:
                self._run_due_jobs()
                time.sleep(_TICK_SECONDS)
        except KeyboardInterrupt:
            self._logger.info("Interrupted — shutting down.")
        finally:
            self._running = False
            self._logger.info("Fledge daemon stopped.")

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_due_jobs(self) -> None:
        for job_name, schedule in self._scheduler.due_jobs():
            self._logger.info("Running job: %s", job_name)
            job_cfg = self._scheduler.get_job_config(job_name)
            result = self._runner.run(job_cfg)
            schedule.mark_ran()

            entry = HistoryEntry.from_result(job_name, result)
            self._history.record(entry)

            if result.success:
                self._logger.info("Job %s completed (rc=%d)", job_name, result.returncode)
            else:
                self._logger.warning(
                    "Job %s failed (rc=%d): %s", job_name, result.returncode, result.output
                )
