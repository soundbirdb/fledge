"""Tests for fledge.budget."""
import time
import pytest
from fledge.budget import BudgetPolicy, BudgetTracker


class TestBudgetPolicy:
    def test_defaults(self):
        p = BudgetPolicy()
        assert p.max_runs == 0
        assert p.window_seconds == 3600
        assert not p.enabled

    def test_from_dict_full(self):
        p = BudgetPolicy.from_dict({"budget": {"max_runs": 10, "window_seconds": 60}})
        assert p.max_runs == 10
        assert p.window_seconds == 60
        assert p.enabled

    def test_from_dict_empty(self):
        p = BudgetPolicy.from_dict({})
        assert p.max_runs == 0
        assert not p.enabled

    def test_from_dict_negative_max_runs_clamped(self):
        p = BudgetPolicy.from_dict({"budget": {"max_runs": -5}})
        assert p.max_runs == 0

    def test_from_dict_zero_window_clamped(self):
        p = BudgetPolicy.from_dict({"budget": {"max_runs": 5, "window_seconds": 0}})
        assert p.window_seconds == 1

    def test_from_dict_string_coerced(self):
        p = BudgetPolicy.from_dict({"budget": {"max_runs": "3", "window_seconds": "120"}})
        assert p.max_runs == 3
        assert p.window_seconds == 120


class TestBudgetTracker:
    def _tracker(self, max_runs=3, window=60):
        policy = BudgetPolicy(max_runs=max_runs, window_seconds=window)
        return BudgetTracker(policy)

    def test_unlimited_always_allowed(self):
        t = BudgetTracker(BudgetPolicy(max_runs=0))
        for _ in range(100):
            assert t.allowed()
            t.record()

    def test_allowed_under_limit(self):
        t = self._tracker(max_runs=3)
        assert t.allowed()
        t.record()
        assert t.allowed()
        t.record()
        assert t.allowed()

    def test_blocked_at_limit(self):
        t = self._tracker(max_runs=2)
        t.record()
        t.record()
        assert not t.allowed()

    def test_current_count_reflects_records(self):
        t = self._tracker(max_runs=5)
        assert t.current_count == 0
        t.record()
        t.record()
        assert t.current_count == 2

    def test_old_entries_evicted(self):
        policy = BudgetPolicy(max_runs=2, window_seconds=1)
        t = BudgetTracker(policy)
        t.record()
        t.record()
        assert not t.allowed()
        # Manually backdate timestamps
        t._timestamps = [ts - 2 for ts in t._timestamps]
        assert t.allowed()
        assert t.current_count == 0
