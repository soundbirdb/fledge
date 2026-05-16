"""Tests for fledge.jitter."""
from unittest.mock import patch

import pytest

from fledge.jitter import Jitter, JitterPolicy


class TestJitterPolicy:
    def test_defaults(self):
        p = JitterPolicy()
        assert p.max_seconds == 0.0
        assert p.enabled is True
        assert p.is_active is False  # 0 seconds => inactive

    def test_from_dict_full(self):
        p = JitterPolicy.from_dict({"max_seconds": 5.0, "enabled": True})
        assert p.max_seconds == 5.0
        assert p.enabled is True
        assert p.is_active is True

    def test_from_dict_empty(self):
        p = JitterPolicy.from_dict({})
        assert p.max_seconds == 0.0
        assert p.is_active is False

    def test_from_dict_zero_disables(self):
        p = JitterPolicy.from_dict({"max_seconds": 0, "enabled": True})
        assert p.is_active is False
        assert p.enabled is False

    def test_from_dict_negative_clamped(self):
        p = JitterPolicy.from_dict({"max_seconds": -3.0})
        assert p.max_seconds == 0.0
        assert p.is_active is False

    def test_from_dict_string_coerced(self):
        p = JitterPolicy.from_dict({"max_seconds": "2.5"})
        assert p.max_seconds == 2.5
        assert p.is_active is True

    def test_from_dict_invalid_string(self):
        p = JitterPolicy.from_dict({"max_seconds": "bad"})
        assert p.max_seconds == 0.0

    def test_explicit_disabled(self):
        p = JitterPolicy.from_dict({"max_seconds": 10.0, "enabled": False})
        assert p.is_active is False


class TestJitter:
    def test_sleep_inactive_returns_zero(self):
        j = Jitter(JitterPolicy(max_seconds=0.0))
        result = j.sleep()
        assert result == 0.0

    def test_sleep_calls_time_sleep(self):
        policy = JitterPolicy(max_seconds=1.0, enabled=True)
        j = Jitter(policy)
        with patch("fledge.jitter.time.sleep") as mock_sleep, \
             patch("fledge.jitter.random.uniform", return_value=0.42):
            result = j.sleep()
        mock_sleep.assert_called_once_with(0.42)
        assert result == pytest.approx(0.42)

    def test_sleep_value_within_bounds(self):
        policy = JitterPolicy(max_seconds=2.0, enabled=True)
        j = Jitter(policy)
        with patch("fledge.jitter.time.sleep"):
            for _ in range(20):
                val = j.sample()
                assert 0.0 <= val <= 2.0

    def test_sample_inactive_returns_zero(self):
        j = Jitter(JitterPolicy())
        assert j.sample() == 0.0

    def test_default_policy_used_when_none(self):
        j = Jitter()
        assert j.sleep() == 0.0
