"""Tests for the Daemon class."""

from unittest.mock import MagicMock, call, patch

import pytest

from fledge.config import FledgeConfig, JobConfig
from fledge.daemon import Daemon
from fledge.runner import JobResult


@pytest.fixture()
def simple_config() -> FledgeConfig:
    jobs = [
        JobConfig(name="ingest", command="echo hello", interval_seconds=60),
    ]
    daemon_cfg = MagicMock()
    daemon_cfg.tick_seconds = 1
    return FledgeConfig(daemon=daemon_cfg, jobs=jobs)


def _make_daemon(config: FledgeConfig) -> Daemon:
    d = Daemon(config)
    # Prevent real sleeping / signal registration in tests
    return d


def test_daemon_initialises_scheduler_and_runner(simple_config):
    d = _make_daemon(simple_config)
    assert len(d.scheduler.schedules) == 1
    assert d.runner is not None


def test_stop_sets_running_false(simple_config):
    d = _make_daemon(simple_config)
    d._running = True
    d.stop()
    assert d._running is False


def test_run_due_jobs_calls_runner_for_due_job(simple_config):
    d = _make_daemon(simple_config)
    mock_result = JobResult(success=True, returncode=0, stdout="", stderr="")
    d.runner.run = MagicMock(return_value=mock_result)

    # All jobs are due immediately on creation
    d._run_due_jobs()

    d.runner.run.assert_called_once()
    called_job = d.runner.run.call_args[0][0]
    assert called_job.name == "ingest"


def test_run_due_jobs_marks_ran_after_execution(simple_config):
    d = _make_daemon(simple_config)
    mock_result = JobResult(success=True, returncode=0, stdout="", stderr="")
    d.runner.run = MagicMock(return_value=mock_result)

    schedule = d.scheduler.schedules[0]
    d._run_due_jobs()

    assert schedule.last_ran is not None


def test_start_stops_after_one_tick(simple_config):
    """Daemon should exit cleanly when _running is set to False."""
    d = _make_daemon(simple_config)
    mock_result = JobResult(success=True, returncode=0, stdout="", stderr="")
    d.runner.run = MagicMock(return_value=mock_result)

    tick_count = 0

    def fake_sleep(_):
        nonlocal tick_count
        tick_count += 1
        d.stop()  # stop after first sleep

    with patch("fledge.daemon.time.sleep", side_effect=fake_sleep), \
         patch("fledge.daemon.signal.signal"):
        d.start()

    assert tick_count == 1
    assert not d._running
