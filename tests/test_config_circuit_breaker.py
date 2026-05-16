"""Tests for circuit_breaker section in FledgeConfig."""

import textwrap
import pytest
from fledge.config import load_config


@pytest.fixture
def config_with_circuit_breaker(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [circuit_breaker]
        failure_threshold = 5
        recovery_timeout = 120.0

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        schedule = "@hourly"
    """))
    return load_config(str(cfg))


@pytest.fixture
def config_no_circuit_breaker(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        schedule = "@hourly"
    """))
    return load_config(str(cfg))


def test_circuit_breaker_parsed(config_with_circuit_breaker):
    cb = config_with_circuit_breaker.circuit_breaker
    assert cb.failure_threshold == 5
    assert cb.recovery_timeout == 120.0


def test_circuit_breaker_defaults_when_absent(config_no_circuit_breaker):
    cb = config_no_circuit_breaker.circuit_breaker
    assert cb.failure_threshold == 3
    assert cb.recovery_timeout == 60.0


def test_circuit_breaker_from_dict_partial():
    from fledge.circuit_breaker import CircuitBreakerPolicy
    p = CircuitBreakerPolicy.from_dict({"failure_threshold": 2})
    assert p.failure_threshold == 2
    assert p.recovery_timeout == 60.0
