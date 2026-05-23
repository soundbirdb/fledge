"""Tests verifying Daemon enforces global execution budget."""
import textwrap
import pytest
from unittest.mock import patch, MagicMock
from fledge.config import load_config
from fledge.daemon import Daemon
from fledge.budget import BudgetPolicy, BudgetTracker


@pytest.fixture
def budget_config(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 1

        [jobs.fetch]
        command = "echo fetch"
        every = 1

        [jobs.fetch.budget]
        max_runs = 2
        window_seconds = 60
    """))
    return load_config(str(cfg))


def _make_daemon(config):
    with patch("fledge.daemon.JobRunner") as MockRunner:
        MockRunner.return_value.run.return_value = MagicMock(success=True, duration=0.1, error=None)
        d = Daemon(config)
        d._runner = MockRunner.return_value
    return d


def test_daemon_has_budget_tracker(budget_config):
    d = _make_daemon(budget_config)
    assert hasattr(d, "_budget_trackers")
    assert "fetch" in d._budget_trackers


def test_budget_tracker_populated(budget_config):
    d = _make_daemon(budget_config)
    tracker = d._budget_trackers["fetch"]
    assert isinstance(tracker, BudgetTracker)
    assert tracker._policy.max_runs == 2


def test_budget_blocks_job_after_limit(budget_config):
    d = _make_daemon(budget_config)
    tracker = d._budget_trackers["fetch"]
    # Exhaust the budget
    tracker.record()
    tracker.record()
    assert not tracker.allowed()


def test_budget_allows_job_within_limit(budget_config):
    d = _make_daemon(budget_config)
    tracker = d._budget_trackers["fetch"]
    tracker.record()
    assert tracker.allowed()
