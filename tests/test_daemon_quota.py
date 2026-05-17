"""Tests that the Daemon respects per-job run quotas."""

import textwrap
import pytest
from unittest.mock import MagicMock, patch
from fledge.config import load_config
from fledge.daemon import Daemon
from fledge.quota import QuotaPolicy, QuotaRegistry


@pytest.fixture
def quota_config(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 1

        [[jobs]]
        name = "limited"
        command = "echo limited"
        every = 1

        [jobs.quota]
        max_runs = 1
        window_seconds = 60

        [[jobs]]
        name = "unlimited"
        command = "echo unlimited"
        every = 1
    """))
    return load_config(cfg)


def _make_daemon(config):
    d = Daemon(config)
    return d


def test_daemon_has_quota_registry(quota_config):
    d = _make_daemon(quota_config)
    assert hasattr(d, "quota_registry")
    assert isinstance(d.quota_registry, QuotaRegistry)


def test_quota_registry_populated(quota_config):
    d = _make_daemon(quota_config)
    tracker = d.quota_registry.get("limited")
    assert tracker is not None
    assert tracker._policy.max_runs == 1


def test_quota_blocks_job_after_limit(quota_config):
    d = _make_daemon(quota_config)
    # exhaust quota for 'limited'
    d.quota_registry.get("limited").record()
    assert not d.quota_registry.allowed("limited")


def test_unlimited_job_always_passes(quota_config):
    d = _make_daemon(quota_config)
    for _ in range(20):
        d.quota_registry.record("unlimited")
    assert d.quota_registry.allowed("unlimited")


def test_run_due_jobs_skips_quota_exceeded(quota_config):
    d = _make_daemon(quota_config)
    # exhaust 'limited' quota
    d.quota_registry.get("limited").record()

    executed = []
    original_run = d._runner.run

    def fake_run(job):
        executed.append(job.name)
        return MagicMock(success=True, job_name=job.name, duration=0.0,
                         output="", error="", attempts=1)

    d._runner.run = fake_run

    # force all jobs due
    for js in d._scheduler._schedules.values():
        js._last_run = None

    d._run_due_jobs()
    assert "limited" not in executed
    assert "unlimited" in executed
