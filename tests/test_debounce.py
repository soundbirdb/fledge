"""Tests for fledge.debounce."""

from __future__ import annotations

import time

import pytest

from fledge.debounce import DebouncePolicy, DebounceTracker


class TestDebouncePolicy:
    def test_defaults(self):
        p = DebouncePolicy()
        assert p.seconds == 0.0
        assert not p.enabled

    def test_from_dict_full(self):
        p = DebouncePolicy.from_dict({"debounce": {"seconds": 5.0}})
        assert p.seconds == 5.0
        assert p.enabled

    def test_from_dict_empty(self):
        p = DebouncePolicy.from_dict({})
        assert p.seconds == 0.0
        assert not p.enabled

    def test_from_dict_negative_clamped(self):
        p = DebouncePolicy.from_dict({"debounce": {"seconds": -3.0}})
        assert p.seconds == 0.0
        assert not p.enabled

    def test_from_dict_zero_disables(self):
        p = DebouncePolicy.from_dict({"debounce": {"seconds": 0}})
        assert not p.enabled

    def test_from_dict_string_coerced(self):
        p = DebouncePolicy.from_dict({"debounce": {"seconds": "2"}})
        assert p.seconds == 2.0


class TestDebounceTracker:
    def test_allow_without_trigger_returns_false(self):
        tracker = DebounceTracker()
        policy = DebouncePolicy(seconds=1.0)
        assert tracker.allow("job_a", policy) is False

    def test_allow_immediately_after_trigger_returns_false(self):
        tracker = DebounceTracker()
        policy = DebouncePolicy(seconds=60.0)
        tracker.trigger("job_a", policy)
        assert tracker.allow("job_a", policy) is False

    def test_allow_after_quiet_period_returns_true(self):
        tracker = DebounceTracker()
        policy = DebouncePolicy(seconds=0.05)
        tracker.trigger("job_a", policy)
        time.sleep(0.1)
        assert tracker.allow("job_a", policy) is True

    def test_allow_clears_pending_after_fire(self):
        tracker = DebounceTracker()
        policy = DebouncePolicy(seconds=0.05)
        tracker.trigger("job_a", policy)
        time.sleep(0.1)
        assert tracker.allow("job_a", policy) is True
        # Second call without re-trigger should be False
        assert tracker.allow("job_a", policy) is False

    def test_disabled_policy_always_allows(self):
        tracker = DebounceTracker()
        policy = DebouncePolicy(seconds=0.0)
        assert tracker.allow("job_a", policy) is True

    def test_disabled_policy_trigger_is_noop(self):
        tracker = DebounceTracker()
        policy = DebouncePolicy(seconds=0.0)
        tracker.trigger("job_a", policy)
        assert tracker._pending == {}

    def test_reset_clears_state(self):
        tracker = DebounceTracker()
        policy = DebouncePolicy(seconds=60.0)
        tracker.trigger("job_a", policy)
        tracker.reset("job_a")
        assert tracker.allow("job_a", policy) is False
        assert "job_a" not in tracker._pending

    def test_independent_jobs(self):
        tracker = DebounceTracker()
        policy = DebouncePolicy(seconds=0.05)
        tracker.trigger("job_a", policy)
        tracker.trigger("job_b", policy)
        time.sleep(0.1)
        assert tracker.allow("job_a", policy) is True
        assert tracker.allow("job_b", policy) is True
