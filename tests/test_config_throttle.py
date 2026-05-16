"""Integration tests: throttle section parsed from TOML config."""

from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config
from fledge.throttle import ThrottlePolicy


TOML_WITH_THROTTLE = textwrap.dedent("""\
    [daemon]
    tick_interval = 5

    [[jobs]]
    name = "fast_job"
    command = "echo fast"
    schedule = "@every 60s"

    [jobs.throttle]
    min_interval = 120

    [[jobs]]
    name = "slow_job"
    command = "echo slow"
    schedule = "@every 300s"
""")

TOML_NO_THROTTLE = textwrap.dedent("""\
    [daemon]
    tick_interval = 5

    [[jobs]]
    name = "only_job"
    command = "echo hi"
    schedule = "@every 60s"
""")


@pytest.fixture()
def config_with_throttle(tmp_path):
    p = tmp_path / "fledge.toml"
    p.write_text(TOML_WITH_THROTTLE)
    return load_config(str(p))


@pytest.fixture()
def config_no_throttle(tmp_path):
    p = tmp_path / "fledge.toml"
    p.write_text(TOML_NO_THROTTLE)
    return load_config(str(p))


def test_throttle_parsed(config_with_throttle):
    job = config_with_throttle.jobs[0]
    assert job.name == "fast_job"
    throttle = ThrottlePolicy.from_dict(job.throttle if hasattr(job, "throttle") and job.throttle else {})
    # If config exposes throttle dict directly:
    raw = getattr(job, "throttle", {}) or {}
    policy = ThrottlePolicy.from_dict(raw)
    assert policy.min_interval == 120.0
    assert policy.enabled


def test_throttle_defaults_when_section_absent(config_no_throttle):
    job = config_no_throttle.jobs[0]
    raw = getattr(job, "throttle", {}) or {}
    policy = ThrottlePolicy.from_dict(raw)
    assert not policy.enabled
    assert policy.min_interval == 0.0


def test_second_job_has_no_throttle(config_with_throttle):
    job = config_with_throttle.jobs[1]
    assert job.name == "slow_job"
    raw = getattr(job, "throttle", {}) or {}
    policy = ThrottlePolicy.from_dict(raw)
    assert not policy.enabled
