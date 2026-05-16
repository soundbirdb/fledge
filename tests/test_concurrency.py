"""Tests for fledge.concurrency."""

import threading
import pytest

from fledge.concurrency import ConcurrencyPolicy, ConcurrencyLimiter


class TestConcurrencyPolicy:
    def test_defaults(self):
        p = ConcurrencyPolicy()
        assert p.max_workers == 4

    def test_from_dict_full(self):
        p = ConcurrencyPolicy.from_dict({"max_workers": 8})
        assert p.max_workers == 8

    def test_from_dict_empty(self):
        p = ConcurrencyPolicy.from_dict({})
        assert p.max_workers == 4

    def test_from_dict_string_coerced(self):
        p = ConcurrencyPolicy.from_dict({"max_workers": "2"})
        assert p.max_workers == 2


@pytest.fixture
def limiter():
    return ConcurrencyLimiter(ConcurrencyPolicy(max_workers=2))


class TestConcurrencyLimiter:
    def test_initial_active_count_is_zero(self, limiter):
        assert limiter.active_count == 0

    def test_acquire_returns_true_when_capacity_available(self, limiter):
        assert limiter.acquire("job_a") is True

    def test_acquire_increments_active_count(self, limiter):
        limiter.acquire("job_a")
        assert limiter.active_count == 1

    def test_release_decrements_active_count(self, limiter):
        limiter.acquire("job_a")
        limiter.release("job_a")
        assert limiter.active_count == 0

    def test_acquire_fails_at_capacity(self, limiter):
        limiter.acquire("job_a")
        limiter.acquire("job_b")
        assert limiter.acquire("job_c") is False

    def test_is_at_capacity(self, limiter):
        assert limiter.is_at_capacity() is False
        limiter.acquire("job_a")
        limiter.acquire("job_b")
        assert limiter.is_at_capacity() is True

    def test_release_allows_new_acquire(self, limiter):
        limiter.acquire("job_a")
        limiter.acquire("job_b")
        limiter.release("job_a")
        assert limiter.acquire("job_c") is True

    def test_active_jobs_reflects_state(self, limiter):
        limiter.acquire("job_a")
        limiter.acquire("job_a")
        jobs = limiter.active_jobs()
        assert jobs == {"job_a": 2}

    def test_thread_safety(self):
        policy = ConcurrencyPolicy(max_workers=10)
        lim = ConcurrencyLimiter(policy)
        results = []

        def worker():
            acquired = lim.acquire("job")
            results.append(acquired)
            if acquired:
                lim.release("job")

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert lim.active_count == 0
