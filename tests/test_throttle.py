"""Tests for fledge.throttle."""

from __future__ import annotations

import time

import pytest

from fledge.throttle import Throttle, ThrottlePolicy


# ---------------------------------------------------------------------------
# ThrottlePolicy
# ---------------------------------------------------------------------------

class TestThrottlePolicy:
    def test_defaults(self):
        p = ThrottlePolicy()
        assert p.min_interval == 0.0
        assert not p.enabled

    def test_from_dict_full(self):
        p = ThrottlePolicy.from_dict({"min_interval": 30})
        assert p.min_interval == 30.0
        assert p.enabled

    def test_from_dict_empty(self):
        p = ThrottlePolicy.from_dict({})
        assert p.min_interval == 0.0
        assert not p.enabled

    def test_from_dict_zero_disables(self):
        p = ThrottlePolicy.from_dict({"min_interval": 0})
        assert not p.enabled


# ---------------------------------------------------------------------------
# Throttle
# ---------------------------------------------------------------------------

@pytest.fixture()
def throttle() -> Throttle:
    return Throttle()


class TestThrottle:
    def test_not_throttled_before_first_run(self, throttle):
        policy = ThrottlePolicy(min_interval=60)
        assert not throttle.is_throttled("job_a", policy)

    def test_throttled_immediately_after_record(self, throttle):
        policy = ThrottlePolicy(min_interval=60)
        throttle.record("job_a")
        assert throttle.is_throttled("job_a", policy)

    def test_not_throttled_after_interval_passes(self, throttle):
        policy = ThrottlePolicy(min_interval=0.01)
        throttle.record("job_a")
        time.sleep(0.02)
        assert not throttle.is_throttled("job_a", policy)

    def test_disabled_policy_never_throttles(self, throttle):
        policy = ThrottlePolicy(min_interval=0)
        throttle.record("job_a")
        assert not throttle.is_throttled("job_a", policy)

    def test_last_run_none_before_record(self, throttle):
        assert throttle.last_run("job_a") is None

    def test_last_run_set_after_record(self, throttle):
        throttle.record("job_a")
        assert throttle.last_run("job_a") is not None

    def test_reset_clears_state(self, throttle):
        policy = ThrottlePolicy(min_interval=60)
        throttle.record("job_a")
        throttle.reset("job_a")
        assert not throttle.is_throttled("job_a", policy)
        assert throttle.last_run("job_a") is None

    def test_jobs_are_independent(self, throttle):
        policy = ThrottlePolicy(min_interval=60)
        throttle.record("job_a")
        assert not throttle.is_throttled("job_b", policy)

    def test_record_updates_last_run_timestamp(self, throttle):
        """A second record() call should advance the stored timestamp."""
        throttle.record("job_a")
        first_ts = throttle.last_run("job_a")
        time.sleep(0.01)
        throttle.record("job_a")
        second_ts = throttle.last_run("job_a")
        assert second_ts > first_ts
