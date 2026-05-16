"""Fledge daemon — orchestrates the scheduler and runner."""

import time
from typing import Optional

from fledge.config import FledgeConfig
from fledge.logging_config import get_logger, setup_logging
from fledge.runner import JobRunner
from fledge.scheduler import Scheduler

logger = get_logger("daemon")


class Daemon:
    """Main daemon that ticks the scheduler and dispatches due jobs."""

    def __init__(self, config: FledgeConfig) -> None:
        self._config = config
        self._running = False
        self._scheduler = Scheduler(config.jobs)
        self._runner = JobRunner()

        setup_logging(
            level=config.logging.level,
            log_file=config.logging.log_file,
            max_bytes=config.logging.max_bytes,
            backup_count=config.logging.backup_count,
        )

    def start(self) -> None:
        """Start the daemon loop."""
        logger.info("Fledge daemon starting — %d job(s) registered", len(self._config.jobs))
        self._running = True
        try:
            while self._running:
                self._run_due_jobs()
                time.sleep(self._config.tick_interval)
        except KeyboardInterrupt:
            logger.info("Interrupted — shutting down")
        finally:
            self.stop()

    def stop(self) -> None:
        """Signal the daemon to stop."""
        logger.info("Fledge daemon stopped")
        self._running = False

    def _run_due_jobs(self) -> None:
        due = self._scheduler.due_jobs()
        for schedule in due:
            logger.info("Running job: %s", schedule.job.name)
            result = self._runner.run(schedule.job)
            schedule.mark_ran()
            if result.success:
                logger.info(
                    "Job '%s' succeeded in %.2fs", schedule.job.name, result.elapsed
                )
            else:
                logger.error(
                    "Job '%s' failed (exit=%s): %s",
                    schedule.job.name,
                    result.returncode,
                    result.stderr.strip() if result.stderr else "(no stderr)",
                )
