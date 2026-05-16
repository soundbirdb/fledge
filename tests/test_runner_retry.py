"""Integration-style tests verifying JobRunner honours RetryPolicy."""

import pytest
from unittest.mock import patch, MagicMock
from fledge.runner import JobRunner, JobResult
from fledge.config import JobConfig
from fledge.retry import RetryPolicy


def _make_job(max_attempts=1, delay_seconds=0.0, backoff_factor=1.0):
    return JobConfig(
        name="test-job",
        command="echo hello",
        interval_seconds=60,
        retry=RetryPolicy(
            max_attempts=max_attempts,
            delay_seconds=delay_seconds,
            backoff_factor=backoff_factor,
        ),
    )


class TestJobRunnerRetry:
    def test_no_retry_on_success(self):
        job = _make_job(max_attempts=3)
        runner = JobRunner()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            result = runner.run(job)
        assert result.success is True
        assert mock_run.call_count == 1

    def test_retries_on_failure(self):
        job = _make_job(max_attempts=3, delay_seconds=0.0)
        runner = JobRunner()
        with patch("subprocess.run") as mock_run, patch(
            "fledge.retry.time.sleep"
        ) as mock_sleep:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="err")
            result = runner.run(job)
        assert result.success is False
        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2

    def test_succeeds_on_second_attempt(self):
        job = _make_job(max_attempts=3, delay_seconds=0.0)
        runner = JobRunner()
        responses = [
            MagicMock(returncode=1, stdout="", stderr="fail"),
            MagicMock(returncode=0, stdout="ok", stderr=""),
        ]
        with patch("subprocess.run", side_effect=responses), patch(
            "fledge.retry.time.sleep"
        ):
            result = runner.run(job)
        assert result.success is True

    def test_single_attempt_no_sleep(self):
        job = _make_job(max_attempts=1)
        runner = JobRunner()
        with patch("subprocess.run") as mock_run, patch(
            "fledge.retry.time.sleep"
        ) as mock_sleep:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="err")
            result = runner.run(job)
        assert result.success is False
        mock_sleep.assert_not_called()
