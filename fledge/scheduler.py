import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from fledge.config import JobConfig

logger = logging.getLogger(__name__)


class JobSchedule:
    """Tracks next-run time for a single job."""

    def __init__(self, job: JobConfig) -> None:
        self.job = job
        self.last_run: Optional[datetime] = None
        self.next_run: datetime = datetime.utcnow()

    def is_due(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return now >= self.next_run

    def mark_ran(self, ran_at: Optional[datetime] = None) -> None:
        self.last_run = ran_at or datetime.utcnow()
        self.next_run = self.last_run + timedelta(seconds=self.job.interval)


class Scheduler:
    """Determines which jobs are due to run based on their intervals."""

    def __init__(self, jobs: list[JobConfig]) -> None:
        self._schedules: Dict[str, JobSchedule] = {
            job.name: JobSchedule(job) for job in jobs
        }

    def due_jobs(self, now: Optional[datetime] = None) -> list[JobConfig]:
        """Return jobs whose next_run time has been reached."""
        now = now or datetime.utcnow()
        due = []
        for schedule in self._schedules.values():
            if schedule.is_due(now):
                due.append(schedule.job)
        return due

    def mark_ran(self, job_name: str, ran_at: Optional[datetime] = None) -> None:
        """Record that a job has just executed."""
        if job_name not in self._schedules:
            raise KeyError(f"Unknown job: {job_name!r}")
        self._schedules[job_name].mark_ran(ran_at)

    def seconds_until_next(self, now: Optional[datetime] = None) -> float:
        """Return seconds until the earliest next_run across all jobs."""
        now = now or datetime.utcnow()
        if not self._schedules:
            return 1.0
        earliest = min(s.next_run for s in self._schedules.values())
        delta = (earliest - now).total_seconds()
        return max(0.0, delta)
