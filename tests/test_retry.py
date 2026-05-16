"""Tests for fledge.retry module."""

import pytest
from fledge.retry import RetryPolicy, run_with_retry


class TestRetryPolicy:
    def test_defaults(self):
        p = RetryPolicy()
        assert p.max_attempts == 1
        assert p.delay_seconds == 5.0
        assert p.backoff_factor == 1.0

    def test_from_dict_full(self):
        p = RetryPolicy.from_dict(
            {"max_attempts": 3, "delay_seconds": 2.0, "backoff_factor": 2.0}
        )
        assert p.max_attempts == 3
        assert p.delay_seconds == 2.0
        assert p.backoff_factor == 2.0

    def test_from_dict_partial(self):
        p = RetryPolicy.from_dict({"max_attempts": 4})
        assert p.max_attempts == 4
        assert p.delay_seconds == 5.0

    def test_from_dict_empty(self):
        p = RetryPolicy.from_dict({})
        assert p.max_attempts == 1

    def test_delays_no_retry(self):
        p = RetryPolicy(max_attempts=1)
        assert list(p.delays()) == []

    def test_delays_flat(self):
        p = RetryPolicy(max_attempts=3, delay_seconds=4.0, backoff_factor=1.0)
        assert list(p.delays()) == [4.0, 4.0]

    def test_delays_backoff(self):
        p = RetryPolicy(max_attempts=3, delay_seconds=2.0, backoff_factor=2.0)
        assert list(p.delays()) == [2.0, 4.0]


class TestRunWithRetry:
    def _no_sleep(self, seconds):
        self.slept.append(seconds)

    def setup_method(self):
        self.slept = []

    def test_succeeds_first_attempt(self):
        policy = RetryPolicy(max_attempts=3, delay_seconds=1.0)
        ok, attempts = run_with_retry(lambda: True, policy, self._no_sleep)
        assert ok is True
        assert attempts == 1
        assert self.slept == []

    def test_fails_all_attempts(self):
        policy = RetryPolicy(max_attempts=3, delay_seconds=1.0)
        ok, attempts = run_with_retry(lambda: False, policy, self._no_sleep)
        assert ok is False
        assert attempts == 3
        assert len(self.slept) == 2

    def test_succeeds_on_second_attempt(self):
        results = [False, True]
        policy = RetryPolicy(max_attempts=3, delay_seconds=2.0)
        ok, attempts = run_with_retry(
            lambda: results.pop(0), policy, self._no_sleep
        )
        assert ok is True
        assert attempts == 2
        assert self.slept == [2.0]

    def test_single_attempt_no_sleep(self):
        policy = RetryPolicy(max_attempts=1)
        ok, attempts = run_with_retry(lambda: False, policy, self._no_sleep)
        assert ok is False
        assert attempts == 1
        assert self.slept == []

    def test_backoff_delays_applied(self):
        policy = RetryPolicy(max_attempts=3, delay_seconds=1.0, backoff_factor=3.0)
        run_with_retry(lambda: False, policy, self._no_sleep)
        assert self.slept == [1.0, 3.0]
