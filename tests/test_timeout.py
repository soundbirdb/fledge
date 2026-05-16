"""Tests for fledge.timeout."""
from __future__ import annotations

import time
import pytest

from fledge.timeout import TimeoutPolicy, JobTimeoutError, run_with_timeout


class TestTimeoutPolicy:
    def test_defaults(self):
        p = TimeoutPolicy()
        assert p.seconds == 0
        assert not p.enabled

    def test_from_dict_full(self):
        p = TimeoutPolicy.from_dict({"seconds": 30})
        assert p.seconds == 30
        assert p.enabled

    def test_from_dict_empty(self):
        p = TimeoutPolicy.from_dict({})
        assert p.seconds == 0
        assert not p.enabled

    def test_from_dict_negative_clamped_to_zero(self):
        p = TimeoutPolicy.from_dict({"seconds": -5})
        assert p.seconds == 0
        assert not p.enabled

    def test_from_dict_string_coerced(self):
        p = TimeoutPolicy.from_dict({"seconds": "10"})
        assert p.seconds == 10


class TestRunWithTimeout:
    def test_no_timeout_runs_normally(self):
        policy = TimeoutPolicy(seconds=0)
        result = run_with_timeout(lambda: 42, policy)
        assert result == 42

    def test_fast_job_completes_within_timeout(self):
        policy = TimeoutPolicy(seconds=5)
        result = run_with_timeout(lambda: "ok", policy)
        assert result == "ok"

    def test_slow_job_raises_timeout_error(self):
        policy = TimeoutPolicy(seconds=1)
        with pytest.raises(JobTimeoutError):
            run_with_timeout(lambda: time.sleep(10), policy)

    def test_alarm_is_cleared_after_success(self):
        import signal
        policy = TimeoutPolicy(seconds=5)
        run_with_timeout(lambda: None, policy)
        # Alarm should be cancelled; remaining time should be 0
        remaining = signal.alarm(0)
        assert remaining == 0

    def test_alarm_is_cleared_after_timeout(self):
        import signal
        policy = TimeoutPolicy(seconds=1)
        with pytest.raises(JobTimeoutError):
            run_with_timeout(lambda: time.sleep(10), policy)
        remaining = signal.alarm(0)
        assert remaining == 0
