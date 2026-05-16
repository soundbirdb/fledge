"""Tests verifying the daemon respects circuit breaker state."""

import pytest
from unittest.mock import MagicMock, patch
from fledge.circuit_breaker import CircuitBreakerPolicy, CircuitBreakerRegistry
from fledge.config import DaemonConfig, FledgeConfig, JobConfig
from fledge.daemon import Daemon


@pytest.fixture
def simple_config():
    job = JobConfig(name="fetch", command="python fetch.py", schedule="@hourly")
    return FledgeConfig(
        daemon=DaemonConfig(interval=10),
        jobs=[job],
        circuit_breaker=CircuitBreakerPolicy(failure_threshold=2, recovery_timeout=60.0),
    )


def _make_daemon(cfg):
    d = Daemon(cfg)
    d._runner = MagicMock()
    return d


def test_daemon_has_circuit_breaker_registry(simple_config):
    d = _make_daemon(simple_config)
    assert hasattr(d, "_circuit_breakers")
    assert isinstance(d._circuit_breakers, CircuitBreakerRegistry)


def test_open_circuit_skips_job(simple_config):
    d = _make_daemon(simple_config)
    # trip the breaker for 'fetch'
    cb = d._circuit_breakers.get("fetch")
    cb.record_failure()
    cb.record_failure()  # threshold=2, now OPEN

    with patch.object(d._scheduler, "due_jobs", return_value=[simple_config.jobs[0]]):
        d._run_due_jobs()

    d._runner.run.assert_not_called()


def test_closed_circuit_runs_job(simple_config):
    d = _make_daemon(simple_config)
    result = MagicMock(success=True)
    d._runner.run.return_value = result

    with patch.object(d._scheduler, "due_jobs", return_value=[simple_config.jobs[0]]):
        d._run_due_jobs()

    d._runner.run.assert_called_once()


def test_successful_run_records_success_on_breaker(simple_config):
    d = _make_daemon(simple_config)
    result = MagicMock(success=True)
    d._runner.run.return_value = result

    with patch.object(d._scheduler, "due_jobs", return_value=[simple_config.jobs[0]]):
        d._run_due_jobs()

    cb = d._circuit_breakers.get("fetch")
    assert cb._failure_count == 0


def test_failed_run_records_failure_on_breaker(simple_config):
    d = _make_daemon(simple_config)
    result = MagicMock(success=False)
    d._runner.run.return_value = result

    with patch.object(d._scheduler, "due_jobs", return_value=[simple_config.jobs[0]]):
        d._run_due_jobs()

    cb = d._circuit_breakers.get("fetch")
    assert cb._failure_count == 1
