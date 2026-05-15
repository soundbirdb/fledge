from datetime import datetime, timedelta

import pytest

from fledge.config import JobConfig
from fledge.scheduler import JobSchedule, Scheduler


@pytest.fixture
def sample_jobs():
    return [
        JobConfig(name="alpha", command="echo alpha", interval=60),
        JobConfig(name="beta", command="echo beta", interval=120),
    ]


@pytest.fixture
def scheduler(sample_jobs):
    return Scheduler(sample_jobs)


class TestJobSchedule:
    def test_is_due_immediately_on_creation(self):
        job = JobConfig(name="x", command="echo x", interval=30)
        schedule = JobSchedule(job)
        assert schedule.is_due()

    def test_not_due_after_mark_ran(self):
        job = JobConfig(name="x", command="echo x", interval=60)
        schedule = JobSchedule(job)
        schedule.mark_ran()
        assert not schedule.is_due()

    def test_next_run_advances_by_interval(self):
        job = JobConfig(name="x", command="echo x", interval=90)
        schedule = JobSchedule(job)
        before = datetime.utcnow()
        schedule.mark_ran(before)
        expected = before + timedelta(seconds=90)
        assert schedule.next_run == expected

    def test_is_due_after_interval_passes(self):
        job = JobConfig(name="x", command="echo x", interval=60)
        schedule = JobSchedule(job)
        ran_at = datetime.utcnow() - timedelta(seconds=61)
        schedule.mark_ran(ran_at)
        assert schedule.is_due()


class TestScheduler:
    def test_all_jobs_due_on_creation(self, scheduler, sample_jobs):
        due = scheduler.due_jobs()
        assert len(due) == len(sample_jobs)

    def test_no_jobs_due_after_mark_ran(self, scheduler, sample_jobs):
        now = datetime.utcnow()
        for job in sample_jobs:
            scheduler.mark_ran(job.name, now)
        assert scheduler.due_jobs(now) == []

    def test_only_expired_job_is_due(self, scheduler, sample_jobs):
        now = datetime.utcnow()
        # mark alpha as ran 65 seconds ago (interval=60 → due again)
        scheduler.mark_ran("alpha", now - timedelta(seconds=65))
        # mark beta as ran 10 seconds ago (interval=120 → not due)
        scheduler.mark_ran("beta", now - timedelta(seconds=10))
        due = scheduler.due_jobs(now)
        assert len(due) == 1
        assert due[0].name == "alpha"

    def test_mark_ran_unknown_job_raises(self, scheduler):
        with pytest.raises(KeyError, match="unknown"):
            scheduler.mark_ran("unknown")

    def test_seconds_until_next_is_non_negative(self, scheduler, sample_jobs):
        now = datetime.utcnow()
        for job in sample_jobs:
            scheduler.mark_ran(job.name, now)
        secs = scheduler.seconds_until_next(now)
        assert secs >= 0.0

    def test_seconds_until_next_empty_scheduler(self):
        s = Scheduler([])
        assert s.seconds_until_next() == 1.0
