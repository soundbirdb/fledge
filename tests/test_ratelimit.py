"""Tests for fledge.ratelimit."""

from __future__ import annotations

import time

import pytest

from fledge.ratelimit import RateLimitPolicy, RateLimiter, RateLimiterRegistry


# ---------------------------------------------------------------------------
# RateLimitPolicy
# ---------------------------------------------------------------------------

class TestRateLimitPolicy:
    def test_defaults(self):
        p = RateLimitPolicy()
        assert p.max_calls == 0
        assert p.window_seconds == 60
        assert not p.enabled

    def test_from_dict_full(self):
        p = RateLimitPolicy.from_dict({"max_calls": "5", "window_seconds": "30"})
        assert p.max_calls == 5
        assert p.window_seconds == 30
        assert p.enabled

    def test_from_dict_empty(self):
        p = RateLimitPolicy.from_dict({})
        assert p.max_calls == 0
        assert not p.enabled

    def test_from_dict_zero_disables(self):
        p = RateLimitPolicy.from_dict({"max_calls": 0})
        assert not p.enabled


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def _limiter(self, max_calls=3, window_seconds=60):
        policy = RateLimitPolicy(max_calls=max_calls, window_seconds=window_seconds)
        return RateLimiter(policy)

    def test_disabled_always_allowed(self):
        limiter = RateLimiter(RateLimitPolicy(max_calls=0))
        for _ in range(100):
            assert limiter.is_allowed()

    def test_allowed_until_limit(self):
        limiter = self._limiter(max_calls=3)
        for _ in range(3):
            assert limiter.is_allowed()
            limiter.record_call()
        assert not limiter.is_allowed()

    def test_remaining_decrements(self):
        limiter = self._limiter(max_calls=3)
        assert limiter.remaining() == 3
        limiter.record_call()
        assert limiter.remaining() == 2

    def test_remaining_unlimited_when_disabled(self):
        limiter = RateLimiter(RateLimitPolicy(max_calls=0))
        assert limiter.remaining() == -1

    def test_window_eviction(self, monkeypatch):
        """Calls older than window_seconds should be evicted."""
        limiter = self._limiter(max_calls=2, window_seconds=10)
        base = 1_000.0
        monkeypatch.setattr(time, "monotonic", lambda: base)
        limiter.record_call()
        limiter.record_call()
        assert not limiter.is_allowed()

        # Advance time beyond the window
        monkeypatch.setattr(time, "monotonic", lambda: base + 11)
        assert limiter.is_allowed()


# ---------------------------------------------------------------------------
# RateLimiterRegistry
# ---------------------------------------------------------------------------

class TestRateLimiterRegistry:
    def test_returns_same_instance_for_same_name(self):
        registry = RateLimiterRegistry()
        policy = RateLimitPolicy(max_calls=5)
        a = registry.get("job_a", policy)
        b = registry.get("job_a", policy)
        assert a is b

    def test_different_names_get_different_limiters(self):
        registry = RateLimiterRegistry()
        policy = RateLimitPolicy(max_calls=5)
        a = registry.get("job_a", policy)
        b = registry.get("job_b", policy)
        assert a is not b
