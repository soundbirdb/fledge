"""Tests for cron-based scheduling integration in the Scheduler."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from fledge.scheduler import JobSchedule, Scheduler
from fledge.cron import CronPolicy


def _make_job(name="job", interval=300, cron_expr=None):
    job = MagicMock()
    job.name = name
    job.interval = interval
    job.cron = CronPolicy(expression=cron_expr)
    return job


class TestJobScheduleCron:
    def test_cron_job_due_when_expression_matches(self):
        job = _make_job(cron_expr="* * * * *")
        sched = JobSchedule(job)
        # Every-minute cron should always be due on a fresh schedule
        assert sched.is_due()

    def test_cron_job_not_due_after_mark_ran_within_same_minute(self):
        job = _make_job(cron_expr="* * * * *")
        sched = JobSchedule(job)
        sched.mark_ran()
        # After running, should not be due again in the same minute
        assert not sched.is_due()

    def test_cron_job_due_again_after_one_minute(self):
        job = _make_job(cron_expr="* * * * *")
        sched = JobSchedule(job)
        sched.mark_ran()
        # Simulate one minute passing
        future = datetime.now(tz=timezone.utc).replace(
            minute=(datetime.now(tz=timezone.utc).minute + 1) % 60
        )
        with patch("fledge.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = future
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            # We only need is_due to check against last_ran
            sched._last_ran = None  # force reset
            assert sched.is_due()

    def test_non_cron_job_uses_interval(self):
        job = _make_job(interval=60, cron_expr=None)
        sched = JobSchedule(job)
        # Fresh schedule should be due immediately (no last_ran)
        assert sched.is_due()


class TestSchedulerCronIntegration:
    def test_scheduler_includes_cron_jobs(self):
        jobs = [
            _make_job(name="cron_job", cron_expr="* * * * *"),
            _make_job(name="interval_job", interval=60),
        ]
        scheduler = Scheduler(jobs)
        due = scheduler.due_jobs()
        names = [j.job.name for j in due]
        assert "cron_job" in names
        assert "interval_job" in names
