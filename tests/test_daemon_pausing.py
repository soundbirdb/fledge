"""Tests verifying that the Daemon integrates PauseRegistry correctly."""

from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config
from fledge.daemon import Daemon
from fledge.pausing import PauseRegistry


TOML = textwrap.dedent("""
    [daemon]
    interval = 1

    [[jobs]]
    name = "active_job"
    command = "echo active"
    every = 1

    [[jobs]]
    name = "paused_job"
    command = "echo paused"
    every = 1

    [jobs.pause]
    paused = true
""")


@pytest.fixture
def pause_config(tmp_path):
    p = tmp_path / "fledge.toml"
    p.write_text(TOML)
    return load_config(str(p))


def _make_daemon(cfg):
    return Daemon(cfg)


def test_daemon_has_pause_registry(pause_config):
    d = _make_daemon(pause_config)
    assert hasattr(d, "pause_registry")
    assert isinstance(d.pause_registry, PauseRegistry)


def test_pause_registry_seeded_from_config(pause_config):
    d = _make_daemon(pause_config)
    assert d.pause_registry.is_paused("paused_job") is True
    assert d.pause_registry.is_paused("active_job") is False


def test_paused_job_skipped_during_run_due(pause_config):
    d = _make_daemon(pause_config)
    ran = []

    def fake_run(job):
        from fledge.runner import JobResult
        ran.append(job.name)
        return JobResult(job_name=job.name, success=True, output="", duration=0.0)

    d._runner.run = fake_run
    d._run_due_jobs()

    assert "paused_job" not in ran


def test_active_job_runs_when_due(pause_config):
    d = _make_daemon(pause_config)
    ran = []

    def fake_run(job):
        from fledge.runner import JobResult
        ran.append(job.name)
        return JobResult(job_name=job.name, success=True, output="", duration=0.0)

    d._runner.run = fake_run
    d._run_due_jobs()

    assert "active_job" in ran


def test_runtime_pause_prevents_subsequent_runs(pause_config):
    d = _make_daemon(pause_config)
    ran = []

    def fake_run(job):
        from fledge.runner import JobResult
        ran.append(job.name)
        return JobResult(job_name=job.name, success=True, output="", duration=0.0)

    d._runner.run = fake_run
    d.pause_registry.pause("active_job")
    d._run_due_jobs()

    assert "active_job" not in ran
