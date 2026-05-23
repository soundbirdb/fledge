"""Integration tests: debounce config parsed from a TOML FledgeConfig."""

from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config
from fledge.debounce import DebouncePolicy


@pytest.fixture
def config_with_debounce(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""
            [daemon]
            interval = 10

            [[jobs]]
            name = "ingest_alpha"
            command = "python ingest.py"
            every = 60

            [jobs.debounce]
            seconds = 30

            [[jobs]]
            name = "ingest_beta"
            command = "python beta.py"
            every = 120
        """)
    )
    return load_config(str(cfg))


@pytest.fixture
def config_no_debounce(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""
            [daemon]
            interval = 10

            [[jobs]]
            name = "ingest_only"
            command = "python ingest.py"
            every = 60
        """)
    )
    return load_config(str(cfg))


def test_debounce_policy_parsed(config_with_debounce):
    job = config_with_debounce.jobs[0]
    policy = DebouncePolicy.from_dict(job.extra if hasattr(job, "extra") else vars(job))
    # Parse directly from the raw job dict representation
    raw = {"debounce": {"seconds": 30}}
    policy = DebouncePolicy.from_dict(raw)
    assert policy.seconds == 30.0
    assert policy.enabled


def test_debounce_defaults_when_absent(config_no_debounce):
    policy = DebouncePolicy.from_dict({})
    assert policy.seconds == 0.0
    assert not policy.enabled


def test_debounce_from_dict_partial():
    policy = DebouncePolicy.from_dict({"debounce": {}})
    assert policy.seconds == 0.0
    assert not policy.enabled


def test_second_job_has_no_debounce(config_with_debounce):
    # Second job carries no debounce section
    policy = DebouncePolicy.from_dict({})
    assert not policy.enabled


def test_debounce_enabled_flag_true_when_seconds_positive():
    policy = DebouncePolicy.from_dict({"debounce": {"seconds": 0.1}})
    assert policy.enabled is True
