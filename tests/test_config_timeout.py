"""Integration tests: timeout policy parsed from a full TOML config."""
from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config


@pytest.fixture
def config_with_timeout(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval = 10

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        schedule = "@hourly"

        [jobs.timeout]
        seconds = 60

        [[jobs]]
        name = "report"
        command = "python report.py"
        schedule = "@daily"
    """))
    return cfg


@pytest.fixture
def config_no_timeout(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval = 10

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        schedule = "@hourly"
    """))
    return cfg


def test_timeout_policy_parsed(config_with_timeout):
    from fledge.timeout import TimeoutPolicy
    config = load_config(config_with_timeout)
    job = config.jobs[0]
    assert hasattr(job, "timeout")
    policy = TimeoutPolicy.from_dict(job.timeout if isinstance(job.timeout, dict) else {})
    # Verify the raw value made it through the config
    raw = getattr(job, "timeout", {})
    assert isinstance(raw, dict)
    assert raw.get("seconds") == 60


def test_timeout_defaults_when_section_absent(config_no_timeout):
    from fledge.timeout import TimeoutPolicy
    config = load_config(config_no_timeout)
    job = config.jobs[0]
    raw = getattr(job, "timeout", {})
    policy = TimeoutPolicy.from_dict(raw or {})
    assert not policy.enabled


def test_second_job_has_no_timeout(config_with_timeout):
    from fledge.timeout import TimeoutPolicy
    config = load_config(config_with_timeout)
    job = config.jobs[1]
    raw = getattr(job, "timeout", {})
    policy = TimeoutPolicy.from_dict(raw or {})
    assert not policy.enabled
