"""Tests for fledge.daemon (including history integration)."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from fledge.config import FledgeConfig, JobConfig, LoggingConfig
from fledge.daemon import Daemon
from fledge.history import HistoryEntry
from fledge.runner import JobResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_config():
    job = JobConfig(name="fetch_data", command="echo hello", interval=60)
    return FledgeConfig(
        jobs=[job],
        logging=LoggingConfig(level="INFO", file=None),
    )


def _make_daemon(config, tmp_path):
    history_path = str(tmp_path / "history.jsonl")
    return Daemon(config, history_path=history_path)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_daemon_initialises_scheduler_and_runner(simple_config, tmp_path):
    d = _make_daemon(simple_config, tmp_path)
    assert d._scheduler is not None
    assert d._runner is not None
    assert d._history is not None


def test_stop_sets_running_false(simple_config, tmp_path):
    d = _make_daemon(simple_config, tmp_path)
    d._running = True
    d.stop()
    assert d._running is False


# ---------------------------------------------------------------------------
# _run_due_jobs
# ---------------------------------------------------------------------------

def test_run_due_jobs_calls_runner_for_due_job(simple_config, tmp_path):
    d = _make_daemon(simple_config, tmp_path)
    fake_result = JobResult(success=True, output="ok", returncode=0)
    d._runner.run = MagicMock(return_value=fake_result)
    d._run_due_jobs()
    d._runner.run.assert_called_once()


def test_run_due_jobs_records_history(simple_config, tmp_path):
    d = _make_daemon(simple_config, tmp_path)
    fake_result = JobResult(success=True, output="done", returncode=0)
    d._runner.run = MagicMock(return_value=fake_result)
    d._run_due_jobs()
    entries = d._history.load()
    assert len(entries) == 1
    assert entries[0].job_name == "fetch_data"
    assert entries[0].success is True


def test_run_due_jobs_records_failure(simple_config, tmp_path):
    d = _make_daemon(simple_config, tmp_path)
    fake_result = JobResult(success=False, output="error", returncode=1)
    d._runner.run = MagicMock(return_value=fake_result)
    d._run_due_jobs()
    last = d._history.last_for("fetch_data")
    assert last is not None
    assert last.success is False
    assert last.returncode == 1


def test_no_history_written_when_no_due_jobs(simple_config, tmp_path):
    d = _make_daemon(simple_config, tmp_path)
    # Mark all jobs as just-ran so none are due
    for _, schedule in d._scheduler.due_jobs():
        schedule.mark_ran()
    d._runner.run = MagicMock()
    d._run_due_jobs()
    # Runner should not have been called again
    d._runner.run.assert_not_called()
    # History should still contain only the initial run (from the loop above)
    # — this test just checks no *additional* writes happened
    count_before = len(d._history.load())
    d._run_due_jobs()
    assert len(d._history.load()) == count_before
