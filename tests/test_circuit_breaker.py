"""Tests for the circuit breaker module."""

import time
import pytest
from fledge.circuit_breaker import (
    BreakerState,
    CircuitBreaker,
    CircuitBreakerPolicy,
    CircuitBreakerRegistry,
)


@pytest.fixture
def policy():
    return CircuitBreakerPolicy(failure_threshold=3, recovery_timeout=60.0)


@pytest.fixture
def breaker(policy):
    return CircuitBreaker(policy=policy)


class TestCircuitBreakerPolicy:
    def test_defaults(self):
        p = CircuitBreakerPolicy()
        assert p.failure_threshold == 3
        assert p.recovery_timeout == 60.0

    def test_from_dict_full(self):
        p = CircuitBreakerPolicy.from_dict({"failure_threshold": 5, "recovery_timeout": 30.0})
        assert p.failure_threshold == 5
        assert p.recovery_timeout == 30.0

    def test_from_dict_empty(self):
        p = CircuitBreakerPolicy.from_dict({})
        assert p.failure_threshold == 3
        assert p.recovery_timeout == 60.0


class TestCircuitBreaker:
    def test_initial_state_is_closed(self, breaker):
        assert breaker.state is BreakerState.CLOSED

    def test_allows_request_when_closed(self, breaker):
        assert breaker.allow_request() is True

    def test_opens_after_threshold_failures(self, breaker):
        for _ in range(3):
            breaker.record_failure()
        assert breaker.state is BreakerState.OPEN

    def test_blocks_request_when_open(self, breaker):
        for _ in range(3):
            breaker.record_failure()
        assert breaker.allow_request() is False

    def test_success_resets_to_closed(self, breaker):
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        assert breaker.state is BreakerState.CLOSED
        assert breaker._failure_count == 0

    def test_half_open_after_recovery_timeout(self, policy):
        policy.recovery_timeout = 0.05
        cb = CircuitBreaker(policy=policy)
        for _ in range(3):
            cb.record_failure()
        assert cb.state is BreakerState.OPEN
        time.sleep(0.1)
        assert cb.state is BreakerState.HALF_OPEN

    def test_half_open_allows_request(self, policy):
        policy.recovery_timeout = 0.05
        cb = CircuitBreaker(policy=policy)
        for _ in range(3):
            cb.record_failure()
        time.sleep(0.1)
        assert cb.allow_request() is True


class TestCircuitBreakerRegistry:
    def test_creates_breaker_on_first_access(self, policy):
        registry = CircuitBreakerRegistry(policy)
        cb = registry.get("job_a")
        assert isinstance(cb, CircuitBreaker)

    def test_returns_same_breaker_instance(self, policy):
        registry = CircuitBreakerRegistry(policy)
        assert registry.get("job_a") is registry.get("job_a")

    def test_states_reflects_all_breakers(self, policy):
        registry = CircuitBreakerRegistry(policy)
        registry.get("job_a")
        registry.get("job_b")
        states = registry.states()
        assert states["job_a"] == "closed"
        assert states["job_b"] == "closed"
