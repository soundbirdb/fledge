"""Tests for fledge.metrics."""

import pytest

from fledge.metrics import JobMetrics, MetricsCollector


# ---------------------------------------------------------------------------
# JobMetrics unit tests
# ---------------------------------------------------------------------------

class TestJobMetrics:
    def test_initial_state(self):
        m = JobMetrics(job_name="fetch")
        assert m.total_runs == 0
        assert m.successful_runs == 0
        assert m.failed_runs == 0
        assert m.last_run_at is None
        assert m.last_duration_seconds is None
        assert m.average_duration is None
        assert m.failure_rate == 0.0

    def test_record_success(self):
        m = JobMetrics(job_name="fetch")
        m.record(success=True, duration=1.5)
        assert m.total_runs == 1
        assert m.successful_runs == 1
        assert m.failed_runs == 0
        assert m.last_duration_seconds == pytest.approx(1.5)
        assert m.last_run_at is not None

    def test_record_failure(self):
        m = JobMetrics(job_name="fetch")
        m.record(success=False, duration=0.3)
        assert m.failed_runs == 1
        assert m.successful_runs == 0

    def test_failure_rate(self):
        m = JobMetrics(job_name="fetch")
        m.record(success=True, duration=1.0)
        m.record(success=False, duration=1.0)
        assert m.failure_rate == pytest.approx(0.5)

    def test_average_duration(self):
        m = JobMetrics(job_name="fetch")
        m.record(success=True, duration=2.0)
        m.record(success=True, duration=4.0)
        assert m.average_duration == pytest.approx(3.0)

    def test_multiple_records_accumulate(self):
        m = JobMetrics(job_name="ingest")
        for i in range(5):
            m.record(success=(i % 2 == 0), duration=float(i))
        assert m.total_runs == 5
        assert m.successful_runs == 3  # indices 0, 2, 4
        assert m.failed_runs == 2


# ---------------------------------------------------------------------------
# MetricsCollector unit tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def collector():
    return MetricsCollector()


def test_collector_starts_empty(collector):
    assert collector.all() == {}


def test_collector_creates_entry_on_first_record(collector):
    collector.record("job_a", success=True, duration=0.5)
    assert "job_a" in collector.all()


def test_collector_get_returns_none_for_unknown(collector):
    assert collector.get("missing") is None


def test_collector_get_returns_metrics(collector):
    collector.record("job_b", success=False, duration=1.2)
    m = collector.get("job_b")
    assert m is not None
    assert m.job_name == "job_b"
    assert m.failed_runs == 1


def test_collector_accumulates_across_calls(collector):
    collector.record("job_c", success=True, duration=1.0)
    collector.record("job_c", success=True, duration=3.0)
    m = collector.get("job_c")
    assert m.total_runs == 2
    assert m.average_duration == pytest.approx(2.0)


def test_collector_summary_shape(collector):
    collector.record("alpha", success=True, duration=1.0)
    collector.record("alpha", success=False, duration=2.0)
    collector.record("beta", success=True, duration=0.5)
    rows = collector.summary()
    assert len(rows) == 2
    names = {r["job"] for r in rows}
    assert names == {"alpha", "beta"}
    alpha = next(r for r in rows if r["job"] == "alpha")
    assert alpha["total"] == 2
    assert alpha["fail"] == 1
    assert alpha["failure_rate"] == pytest.approx(0.5)
    assert alpha["avg_duration"] == pytest.approx(1.5)
