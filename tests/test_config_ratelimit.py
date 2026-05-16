"""Integration tests: rate-limit config parsed from a TOML FledgeConfig."""

from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config
from fledge.ratelimit import RateLimitPolicy


@pytest.fixture
def config_with_ratelimit(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval_seconds = 10

        [[jobs]]
        name = "ingest_a"
        command = "python ingest_a.py"
        schedule = "@every 60s"

        [jobs.rate_limit]
        max_calls = 5
        window_seconds = 120

        [[jobs]]
        name = "ingest_b"
        command = "python ingest_b.py"
        schedule = "@every 30s"
    """))
    return load_config(str(cfg))


@pytest.fixture
def config_no_ratelimit(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval_seconds = 10

        [[jobs]]
        name = "ingest_a"
        command = "python ingest_a.py"
        schedule = "@every 60s"
    """))
    return load_config(str(cfg))


def test_ratelimit_policy_parsed(config_with_ratelimit):
    job = config_with_ratelimit.jobs[0]
    policy = RateLimitPolicy.from_dict(job.extra.get("rate_limit", {}))
    assert policy.max_calls == 5
    assert policy.window_seconds == 120
    assert policy.enabled


def test_ratelimit_defaults_when_section_absent(config_no_ratelimit):
    job = config_no_ratelimit.jobs[0]
    policy = RateLimitPolicy.from_dict(job.extra.get("rate_limit", {}))
    assert not policy.enabled
    assert policy.max_calls == 0


def test_second_job_has_no_ratelimit(config_with_ratelimit):
    job = config_with_ratelimit.jobs[1]
    policy = RateLimitPolicy.from_dict(job.extra.get("rate_limit", {}))
    assert not policy.enabled


def test_ratelimit_from_dict_partial():
    policy = RateLimitPolicy.from_dict({"max_calls": 10})
    assert policy.max_calls == 10
    assert policy.window_seconds == 60  # default
