"""Integration: runner pushes to dead-letter queue after retries are exhausted."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fledge.deadletter import DeadLetterQueue
from fledge.retry import RetryPolicy
from fledge.runner import JobResult, JobRunner


def _make_job(name="sink", command="false", interval=60, retry_cfg=None, max_workers=1):
    job = MagicMock()
    job.name = name
    job.command = command
    job.interval = interval
    job.retry = retry_cfg or RetryPolicy(max_attempts=2, backoff=0.0, jitter=0.0)
    job.throttle = MagicMock(enabled=False)
    job.concurrency = MagicMock(max_workers=max_workers)
    job.rate_limit = MagicMock(enabled=False)
    return job


@pytest.fixture
def dlq(tmp_path):
    return DeadLetterQueue(path=str(tmp_path / "dlq.jsonl"))


def _always_fail(command, **kwargs):
    return JobResult(job_name="sink", command=command, success=False, exit_code=1, stderr="err")


def _always_succeed(command, **kwargs):
    return JobResult(job_name="sink", command=command, success=True, exit_code=0, stderr="")


class TestRunnerDeadLetter:
    def test_failed_job_pushed_to_dlq(self, dlq):
        runner = JobRunner(dead_letter_queue=dlq)
        job = _make_job(retry_cfg=RetryPolicy(max_attempts=2, backoff=0.0, jitter=0.0))
        with patch("fledge.runner.JobRunner._execute", side_effect=_always_fail):
            result = runner.run(job)
        assert not result.success
        assert dlq.size == 1
        entry = dlq.load_all()[0]
        assert entry.job_name == "sink"
        assert entry.attempts == 2

    def test_successful_job_not_pushed_to_dlq(self, dlq):
        runner = JobRunner(dead_letter_queue=dlq)
        job = _make_job(retry_cfg=RetryPolicy(max_attempts=1, backoff=0.0, jitter=0.0))
        with patch("fledge.runner.JobRunner._execute", side_effect=_always_succeed):
            result = runner.run(job)
        assert result.success
        assert dlq.size == 0

    def test_no_dlq_does_not_raise(self):
        runner = JobRunner(dead_letter_queue=None)
        job = _make_job(retry_cfg=RetryPolicy(max_attempts=1, backoff=0.0, jitter=0.0))
        with patch("fledge.runner.JobRunner._execute", side_effect=_always_fail):
            result = runner.run(job)
        assert not result.success  # just confirm it ran without error
