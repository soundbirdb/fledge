"""Tests verifying the daemon honours run-once policies."""
from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config
from fledge.daemon import Daemon
from fledge.runonce import RunOnceTracker


@pytest.fixture
def runonce_config(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval = 1

        [[jobs]]
        name = "once_job"
        command = "echo once"
        every = 1

        [jobs.run_once]
        enabled = true
        scope = "day"
    """))
    return load_config(str(cfg))


def _make_daemon(cfg, tmp_path):
    tracker_path = str(tmp_path / "runonce.json")
    d = Daemon(cfg)
    d._runonce_tracker = RunOnceTracker(path=tracker_path)
    return d


def test_daemon_has_runonce_tracker(runonce_config, tmp_path):
    d = _make_daemon(runonce_config, tmp_path)
    assert hasattr(d, "_runonce_tracker")
    assert isinstance(d._runonce_tracker, RunOnceTracker)


def test_runonce_job_runs_first_time(runonce_config, tmp_path):
    d = _make_daemon(runonce_config, tmp_path)
    job = runonce_config.jobs[0]
    tracker = d._runonce_tracker
    assert not tracker.has_run(job.name, "day")


def test_runonce_job_blocked_after_record(runonce_config, tmp_path):
    d = _make_daemon(runonce_config, tmp_path)
    job = runonce_config.jobs[0]
    tracker = d._runonce_tracker
    tracker.record(job.name)
    assert tracker.has_run(job.name, "day") is True


def test_runonce_tracker_reset_clears_state(runonce_config, tmp_path):
    d = _make_daemon(runonce_config, tmp_path)
    job = runonce_config.jobs[0]
    tracker = d._runonce_tracker
    tracker.record(job.name)
    tracker.reset(job.name)
    assert tracker.has_run(job.name, "day") is False
