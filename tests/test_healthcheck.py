"""Tests for fledge.healthcheck."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from fledge.healthcheck import HealthChecker, HealthReport, JobHealth
from fledge.metrics import MetricsCollector, JobMetrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job_metrics(total_runs: int, failures: int, total_duration: float) -> JobMetrics:
    jm = JobMetrics()
    jm.total_runs = total_runs
    jm.failed_runs = failures
    jm.total_duration = total_duration
    jm.last_run_at = time.time() if total_runs else None
    return jm


@pytest.fixture()
def collector() -> MetricsCollector:
    return MetricsCollector()


@pytest.fixture()
def checker(collector: MetricsCollector) -> HealthChecker:
    # Pin start_time so uptime is deterministic-ish
    return HealthChecker(collector, start_time=time.monotonic())


# ---------------------------------------------------------------------------
# HealthChecker.report
# ---------------------------------------------------------------------------

class TestHealthCheckerReport:
    def test_status_unknown_when_no_jobs(self, checker: HealthChecker) -> None:
        report = checker.report()
        assert report.status == "unknown"
        assert report.jobs == {}

    def test_status_ok_when_no_failures(self, collector: MetricsCollector, checker: HealthChecker) -> None:
        collector._data["ingest"] = _make_job_metrics(10, 0, 5.0)
        report = checker.report()
        assert report.status == "ok"

    def test_status_degraded_when_high_failure_rate(self, collector: MetricsCollector, checker: HealthChecker) -> None:
        collector._data["ingest"] = _make_job_metrics(10, 6, 5.0)
        report = checker.report()
        assert report.status == "degraded"

    def test_uptime_is_non_negative(self, checker: HealthChecker) -> None:
        report = checker.report()
        assert report.uptime >= 0.0

    def test_job_health_fields(self, collector: MetricsCollector, checker: HealthChecker) -> None:
        collector._data["fetch"] = _make_job_metrics(4, 1, 8.0)
        report = checker.report()
        jh = report.jobs["fetch"]
        assert jh.name == "fetch"
        assert jh.total_runs == 4
        assert pytest.approx(jh.failure_rate, abs=1e-4) == 0.25
        assert pytest.approx(jh.average_duration, abs=1e-4) == 2.0

    def test_multiple_jobs_one_degraded(self, collector: MetricsCollector, checker: HealthChecker) -> None:
        collector._data["good"] = _make_job_metrics(10, 0, 3.0)
        collector._data["bad"] = _make_job_metrics(10, 8, 3.0)
        report = checker.report()
        assert report.status == "degraded"
        assert "good" in report.jobs
        assert "bad" in report.jobs


# ---------------------------------------------------------------------------
# HealthReport.as_dict
# ---------------------------------------------------------------------------

class TestHealthReportAsDict:
    def test_as_dict_keys(self) -> None:
        report = HealthReport(status="ok", uptime=42.5)
        d = report.as_dict()
        assert set(d.keys()) == {"status", "uptime", "jobs"}
        assert d["status"] == "ok"
        assert d["uptime"] == 42.5

    def test_job_health_as_dict(self) -> None:
        jh = JobHealth(name="j", total_runs=2, failure_rate=0.0, average_duration=1.5, last_run_at=None)
        d = jh.as_dict()
        assert d["name"] == "j"
        assert d["total_runs"] == 2
        assert d["last_run_at"] is None
