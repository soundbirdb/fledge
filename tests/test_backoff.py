"""Tests for fledge.backoff."""
import math
import pytest

from fledge.backoff import BackoffPolicy


class TestBackoffPolicy:
    def test_defaults(self):
        bp = BackoffPolicy()
        assert bp.base_delay == 1.0
        assert bp.multiplier == 2.0
        assert bp.max_delay == 60.0
        assert bp.jitter == 0.0

    def test_from_dict_full(self):
        bp = BackoffPolicy.from_dict(
            {"base_delay": 2.0, "multiplier": 3.0, "max_delay": 120.0, "jitter": 0.1}
        )
        assert bp.base_delay == 2.0
        assert bp.multiplier == 3.0
        assert bp.max_delay == 120.0
        assert bp.jitter == 0.1

    def test_from_dict_empty(self):
        bp = BackoffPolicy.from_dict({})
        assert bp.base_delay == 1.0
        assert bp.multiplier == 2.0

    def test_from_dict_clamps_multiplier_below_one(self):
        bp = BackoffPolicy.from_dict({"multiplier": 0.1})
        assert bp.multiplier == 1.0

    def test_from_dict_clamps_jitter_above_one(self):
        bp = BackoffPolicy.from_dict({"jitter": 5.0})
        assert bp.jitter == 1.0

    def test_from_dict_clamps_base_delay_negative(self):
        bp = BackoffPolicy.from_dict({"base_delay": -3.0})
        assert bp.base_delay == 0.0

    def test_enabled_when_base_delay_positive(self):
        assert BackoffPolicy(base_delay=1.0).enabled is True

    def test_disabled_when_base_delay_zero(self):
        assert BackoffPolicy(base_delay=0.0).enabled is False

    def test_delays_count_matches_max_attempts(self):
        bp = BackoffPolicy(base_delay=1.0, multiplier=2.0, max_delay=60.0)
        result = list(bp.delays(4))
        assert len(result) == 4

    def test_delays_grow_exponentially(self):
        bp = BackoffPolicy(base_delay=1.0, multiplier=2.0, max_delay=1000.0, jitter=0.0)
        result = list(bp.delays(5))
        for i, delay in enumerate(result):
            assert math.isclose(delay, 1.0 * (2.0 ** i), rel_tol=1e-6)

    def test_delays_capped_at_max_delay(self):
        bp = BackoffPolicy(base_delay=10.0, multiplier=10.0, max_delay=50.0, jitter=0.0)
        result = list(bp.delays(4))
        assert all(d <= 50.0 for d in result)

    def test_delays_with_jitter_within_bounds(self):
        bp = BackoffPolicy(base_delay=1.0, multiplier=2.0, max_delay=1000.0, jitter=0.5)
        for delay in bp.delays(6):
            assert delay >= 0.0

    def test_zero_attempts_yields_nothing(self):
        bp = BackoffPolicy()
        assert list(bp.delays(0)) == []
