"""Tests for fledge.quota."""

import time
import pytest
from fledge.quota import QuotaPolicy, QuotaTracker, QuotaRegistry


class TestQuotaPolicy:
    def test_defaults(self):
        p = QuotaPolicy()
        assert p.max_runs == 0
        assert p.window_seconds == 3600
        assert not p.enabled

    def test_from_dict_full(self):
        p = QuotaPolicy.from_dict({"max_runs": 5, "window_seconds": 60})
        assert p.max_runs == 5
        assert p.window_seconds == 60
        assert p.enabled

    def test_from_dict_empty(self):
        p = QuotaPolicy.from_dict({})
        assert p.max_runs == 0
        assert not p.enabled

    def test_from_dict_negative_clamped(self):
        p = QuotaPolicy.from_dict({"max_runs": -3})
        assert p.max_runs == 0

    def test_from_dict_window_below_one_clamped(self):
        p = QuotaPolicy.from_dict({"max_runs": 1, "window_seconds": 0})
        assert p.window_seconds == 1


class TestQuotaTracker:
    def _policy(self, max_runs=3, window=60):
        return QuotaPolicy(max_runs=max_runs, window_seconds=window)

    def test_always_allowed_when_disabled(self):
        tracker = QuotaTracker(QuotaPolicy(max_runs=0))
        for _ in range(100):
            assert tracker.allowed()
            tracker.record()

    def test_allowed_up_to_limit(self):
        tracker = QuotaTracker(self._policy(max_runs=2))
        now = time.monotonic()
        assert tracker.allowed(now)
        tracker.record(now)
        assert tracker.allowed(now)
        tracker.record(now)
        assert not tracker.allowed(now)

    def test_runs_expire_after_window(self):
        tracker = QuotaTracker(self._policy(max_runs=2, window=1))
        past = time.monotonic() - 2          # outside the 1-second window
        tracker.record(past)
        tracker.record(past)
        assert tracker.allowed()             # old entries evicted

    def test_run_count_reflects_window(self):
        tracker = QuotaTracker(self._policy(max_runs=5, window=60))
        now = time.monotonic()
        tracker.record(now)
        tracker.record(now)
        assert tracker.run_count == 2

    def test_record_noop_when_disabled(self):
        tracker = QuotaTracker(QuotaPolicy(max_runs=0))
        tracker.record()
        assert tracker.run_count == 0


class TestQuotaRegistry:
    def _make_registry(self):
        reg = QuotaRegistry()
        reg.register("job_a", QuotaPolicy(max_runs=2, window_seconds=60))
        reg.register("job_b", QuotaPolicy(max_runs=0))
        return reg

    def test_allowed_unknown_job_is_true(self):
        reg = QuotaRegistry()
        assert reg.allowed("ghost")

    def test_allowed_within_quota(self):
        reg = self._make_registry()
        assert reg.allowed("job_a")

    def test_blocked_after_quota_exhausted(self):
        reg = self._make_registry()
        now = time.monotonic()
        reg.get("job_a").record(now)
        reg.get("job_a").record(now)
        assert not reg.allowed("job_a")

    def test_unlimited_job_always_allowed(self):
        reg = self._make_registry()
        for _ in range(50):
            reg.record("job_b")
        assert reg.allowed("job_b")
