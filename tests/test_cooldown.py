"""Tests for fledge.cooldown."""

from __future__ import annotations

import time

import pytest

from fledge.cooldown import CooldownPolicy, CooldownTracker


# ---------------------------------------------------------------------------
# CooldownPolicy
# ---------------------------------------------------------------------------

class TestCooldownPolicy:
    def test_defaults(self):
        p = CooldownPolicy()
        assert p.seconds == 0.0
        assert not p.enabled

    def test_from_dict_full(self):
        p = CooldownPolicy.from_dict({"cooldown": {"seconds": 30}})
        assert p.seconds == 30.0
        assert p.enabled

    def test_from_dict_empty(self):
        p = CooldownPolicy.from_dict({})
        assert p.seconds == 0.0
        assert not p.enabled

    def test_from_dict_zero_disables(self):
        p = CooldownPolicy.from_dict({"cooldown": {"seconds": 0}})
        assert not p.enabled

    def test_from_dict_negative_clamped(self):
        p = CooldownPolicy.from_dict({"cooldown": {"seconds": -5}})
        assert p.seconds == 0.0
        assert not p.enabled

    def test_from_dict_float_seconds(self):
        p = CooldownPolicy.from_dict({"cooldown": {"seconds": 1.5}})
        assert p.seconds == 1.5


# ---------------------------------------------------------------------------
# CooldownTracker
# ---------------------------------------------------------------------------

@pytest.fixture()
def tracker() -> CooldownTracker:
    return CooldownTracker()


@pytest.fixture()
def policy_30s() -> CooldownPolicy:
    return CooldownPolicy(seconds=30.0)


class TestCooldownTracker:
    def test_not_cooling_before_any_success(self, tracker, policy_30s):
        assert not tracker.is_cooling_down("job_a", policy_30s)

    def test_cooling_immediately_after_success(self, tracker, policy_30s):
        tracker.record_success("job_a")
        assert tracker.is_cooling_down("job_a", policy_30s)

    def test_not_cooling_when_policy_disabled(self, tracker):
        policy = CooldownPolicy(seconds=0.0)
        tracker.record_success("job_a")
        assert not tracker.is_cooling_down("job_a", policy)

    def test_not_cooling_after_window_expires(self, tracker):
        policy = CooldownPolicy(seconds=0.05)
        tracker.record_success("job_a")
        time.sleep(0.1)
        assert not tracker.is_cooling_down("job_a", policy)

    def test_remaining_positive_during_cooldown(self, tracker, policy_30s):
        tracker.record_success("job_a")
        rem = tracker.remaining("job_a", policy_30s)
        assert 0.0 < rem <= 30.0

    def test_remaining_zero_before_any_success(self, tracker, policy_30s):
        assert tracker.remaining("job_a", policy_30s) == 0.0

    def test_remaining_zero_when_policy_disabled(self, tracker):
        policy = CooldownPolicy(seconds=0.0)
        tracker.record_success("job_a")
        assert tracker.remaining("job_a", policy) == 0.0

    def test_independent_jobs(self, tracker, policy_30s):
        tracker.record_success("job_a")
        assert tracker.is_cooling_down("job_a", policy_30s)
        assert not tracker.is_cooling_down("job_b", policy_30s)
