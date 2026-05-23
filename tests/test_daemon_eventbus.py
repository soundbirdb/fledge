"""Integration tests: Daemon publishes events via EventBus."""

import types
from unittest.mock import MagicMock, patch

import pytest

from fledge.config import FledgeConfig, DaemonConfig, JobConfig
from fledge.daemon import Daemon
from fledge.eventbus import EventBus, JobEvent


def _make_config(cmd: str = "echo hi") -> FledgeConfig:
    cfg = FledgeConfig.__new__(FledgeConfig)
    cfg.daemon = DaemonConfig(interval=1, max_workers=1)
    cfg.jobs = [
        JobConfig(name="testjob", command=cmd, schedule=0),
    ]
    cfg.logging = MagicMock(level="INFO", file=None)
    cfg.notifier = MagicMock(enabled=False)
    cfg.audit = MagicMock(path=None)
    return cfg


def _make_daemon(cfg=None):
    cfg = cfg or _make_config()
    d = Daemon(cfg)
    return d


class TestDaemonEventBus:
    def test_daemon_exposes_event_bus(self):
        d = _make_daemon()
        assert isinstance(d.event_bus, EventBus)

    def test_successful_job_publishes_started_and_succeeded(self):
        d = _make_daemon()
        events = []
        d.event_bus.subscribe("*", events.append)

        with patch.object(d._runner, "run") as mock_run:
            result = MagicMock()
            result.success = True
            result.job_name = "testjob"
            result.duration = 0.42
            result.error = None
            mock_run.return_value = result
            d._run_due_jobs()

        types_seen = [e.event_type for e in events]
        assert "job.started" in types_seen
        assert "job.succeeded" in types_seen

    def test_failed_job_publishes_started_and_failed(self):
        d = _make_daemon()
        events = []
        d.event_bus.subscribe("*", events.append)

        with patch.object(d._runner, "run") as mock_run:
            result = MagicMock()
            result.success = False
            result.job_name = "testjob"
            result.duration = 0.1
            result.error = "oops"
            mock_run.return_value = result
            d._run_due_jobs()

        types_seen = [e.event_type for e in events]
        assert "job.started" in types_seen
        assert "job.failed" in types_seen

    def test_event_carries_correct_job_name(self):
        d = _make_daemon()
        events = []
        d.event_bus.subscribe("job.succeeded", events.append)

        with patch.object(d._runner, "run") as mock_run:
            result = MagicMock()
            result.success = True
            result.job_name = "testjob"
            result.duration = 0.5
            result.error = None
            mock_run.return_value = result
            d._run_due_jobs()

        assert events[0].job_name == "testjob"
