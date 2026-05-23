"""Tests for the sliding-window rate limiter."""

from __future__ import annotations

import time
import pytest

from fledge.ratelimit_window import SlidingWindowPolicy, SlidingWindowLimiter


class TestSlidingWindowPolicy:
    def test_defaults(self):
        p = SlidingWindowPolicy()
        assert p.max_calls == 0
        assert p.window_seconds == 60.0
        assert not p.enabled

    def test_from_dict_full(self):
        p = SlidingWindowPolicy.from_dict({"sliding_window": {"max_calls": 5, "window_seconds": 30}})
        assert p.max_calls == 5
        assert p.window_seconds == 30.0
        assert p.enabled

    def test_from_dict_empty(self):
        p = SlidingWindowPolicy.from_dict({})
        assert p.max_calls == 0
        assert not p.enabled

    def test_from_dict_negative_max_calls_clamped(self):
        p = SlidingWindowPolicy.from_dict({"sliding_window": {"max_calls": -3}})
        assert p.max_calls == 0
        assert not p.enabled

    def test_from_dict_zero_window_defaults_to_sixty(self):
        p = SlidingWindowPolicy.from_dict({"sliding_window": {"max_calls": 2, "window_seconds": 0}})
        assert p.window_seconds == 60.0

    def test_from_dict_string_coerced(self):
        p = SlidingWindowPolicy.from_dict({"sliding_window": {"max_calls": "10", "window_seconds": "120"}})
        assert p.max_calls == 10
        assert p.window_seconds == 120.0


class TestSlidingWindowLimiter:
    def test_allowed_when_disabled(self):
        limiter = SlidingWindowLimiter()
        policy = SlidingWindowPolicy(max_calls=0)
        assert limiter.is_allowed("job", policy) is True

    def test_first_call_allowed(self):
        limiter = SlidingWindowLimiter()
        policy = SlidingWindowPolicy(max_calls=3, window_seconds=60)
        assert limiter.is_allowed("job", policy) is True

    def test_blocked_after_limit_reached(self):
        limiter = SlidingWindowLimiter()
        policy = SlidingWindowPolicy(max_calls=2, window_seconds=60)
        limiter.record("job")
        limiter.record("job")
        assert limiter.is_allowed("job", policy) is False

    def test_allowed_after_window_expires(self):
        limiter = SlidingWindowLimiter()
        policy = SlidingWindowPolicy(max_calls=1, window_seconds=0.05)
        limiter.record("job")
        assert limiter.is_allowed("job", policy) is False
        time.sleep(0.06)
        assert limiter.is_allowed("job", policy) is True

    def test_remaining_when_disabled(self):
        limiter = SlidingWindowLimiter()
        policy = SlidingWindowPolicy(max_calls=0)
        assert limiter.remaining("job", policy) == -1

    def test_remaining_decrements_on_record(self):
        limiter = SlidingWindowLimiter()
        policy = SlidingWindowPolicy(max_calls=3, window_seconds=60)
        assert limiter.remaining("job", policy) == 3
        limiter.record("job")
        assert limiter.remaining("job", policy) == 2

    def test_remaining_never_negative(self):
        limiter = SlidingWindowLimiter()
        policy = SlidingWindowPolicy(max_calls=1, window_seconds=60)
        limiter.record("job")
        limiter.record("job")
        assert limiter.remaining("job", policy) == 0

    def test_independent_jobs(self):
        limiter = SlidingWindowLimiter()
        policy = SlidingWindowPolicy(max_calls=1, window_seconds=60)
        limiter.record("job_a")
        assert limiter.is_allowed("job_a", policy) is False
        assert limiter.is_allowed("job_b", policy) is True
