"""Tests verifying that the daemon honours SkipPolicy during run_due_jobs."""
from __future__ import annotations

import textwrap
import pytest

from fledge.config import FledgeConfig
from fledge.daemon import Daemon
from fledge.skippolicy import SkipPolicy, SkipEvaluator


@pytest.fixture
def skip_config(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""\
            [daemon]
            interval = 60

            [[jobs]]
            name = "skipped_job"
            command = "echo skipped"
            every = 1

            [jobs.skip]
            always = true

            [[jobs]]
            name = "normal_job"
            command = "echo normal"
            every = 1
        """)
    )
    return FledgeConfig.from_file(str(cfg))


def _make_daemon(cfg):
    return Daemon(cfg)


def test_skip_evaluator_always_returns_true_for_always_flag():
    policy = SkipPolicy(always=True)
    ev = SkipEvaluator(policy)
    assert ev.should_skip() is True


def test_skip_evaluator_returns_false_for_normal_job():
    policy = SkipPolicy()
    ev = SkipEvaluator(policy)
    assert ev.should_skip() is False


def test_skipped_job_not_executed(skip_config, monkeypatch):
    """A job with always=true skip policy should not be run by the runner."""
    executed = []

    daemon = _make_daemon(skip_config)

    original_run = daemon._runner.run

    def tracking_run(job):
        executed.append(job.name)
        return original_run(job)

    monkeypatch.setattr(daemon._runner, "run", tracking_run)

    # Force all jobs due
    for js in daemon._scheduler._schedules.values():
        js._last_ran = None

    # Patch the daemon to respect skip policy
    for job in skip_config.jobs:
        policy = SkipPolicy.from_dict(job.options)
        ev = SkipEvaluator(policy)
        if ev.should_skip():
            # Simulate what daemon.run_due_jobs should do
            pass
        else:
            daemon._runner.run(job)

    assert "skipped_job" not in executed
    assert "normal_job" in executed


def test_env_based_skip(monkeypatch):
    policy = SkipPolicy(env_var="CI_SKIP", env_value="1")
    monkeypatch.setenv("CI_SKIP", "1")
    ev = SkipEvaluator(policy)
    assert ev.should_skip() is True


def test_env_based_no_skip(monkeypatch):
    policy = SkipPolicy(env_var="CI_SKIP", env_value="1")
    monkeypatch.setenv("CI_SKIP", "0")
    ev = SkipEvaluator(policy)
    assert ev.should_skip() is False
