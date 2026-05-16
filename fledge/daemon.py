"""Main daemon loop that ties together config, scheduler, and runner."""

import logging
import signal
import time
from typing import Optional

from fledge.config import FledgeConfig, load_config
from fledge.runner import JobRunner
from fledge.scheduler import Scheduler

logger = logging.getLogger(__name__)


class Daemon:
    """Periodic job queue daemon."""

    def __init__(self, config: FledgeConfig) -> None:
        self.config = config
        self.scheduler = Scheduler(config.jobs)
        self.runner = JobRunner()
        self._running = False

    def start(self) -> None:
        """Start the daemon loop, blocking until stopped."""
        self._running = True
        self._register_signals()
        tick = self.config.daemon.tick_seconds
        logger.info(
            "Fledge daemon starting — %d job(s), tick=%ss",
            len(self.config.jobs),
            tick,
        )
        while self._running:
            self._run_due_jobs()
            time.sleep(tick)
        logger.info("Fledge daemon stopped.")

    def stop(self) -> None:
        """Signal the daemon to stop after the current tick."""
        logger.info("Stop requested.")
        self._running = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_due_jobs(self) -> None:
        for schedule in self.scheduler.due_jobs():
            logger.info("Running job: %s", schedule.job.name)
            result = self.runner.run(schedule.job)
            schedule.mark_ran()
            if result.success:
                logger.info("Job %s completed (exit 0)", schedule.job.name)
            else:
                logger.error(
                    "Job %s failed (exit %s): %s",
                    schedule.job.name,
                    result.returncode,
                    result.stderr.strip() if result.stderr else "",
                )

    def _register_signals(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:  # noqa: ANN001
        logger.info("Received signal %s.", signum)
        self.stop()


def run_from_config_file(path: str) -> None:
    """Convenience entry-point: load config file and start the daemon."""
    config = load_config(path)
    Daemon(config).start()
