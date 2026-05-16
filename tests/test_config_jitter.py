"""Integration tests: jitter policy parsed from a full FledgeConfig."""
import textwrap
import pytest

from fledge.config import load_config
from fledge.jitter import JitterPolicy


@pytest.fixture
def config_with_jitter(tmp_path):
    toml = textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "fetch"
        command = "python fetch.py"
        schedule = "@hourly"

        [jobs.jitter]
        max_seconds = 30.0
        enabled = true

        [[jobs]]
        name = "clean"
        command = "python clean.py"
        schedule = "@daily"
    """)
    p = tmp_path / "fledge.toml"
    p.write_text(toml)
    return load_config(str(p))


@pytest.fixture
def config_no_jitter(tmp_path):
    toml = textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "fetch"
        command = "python fetch.py"
        schedule = "@hourly"
    """)
    p = tmp_path / "fledge.toml"
    p.write_text(toml)
    return load_config(str(p))


def test_jitter_policy_parsed(config_with_jitter):
    job = config_with_jitter.jobs[0]
    policy = JitterPolicy.from_dict(job.extra.get("jitter", {}))
    assert policy.max_seconds == 30.0
    assert policy.is_active is True


def test_jitter_defaults_when_section_absent(config_no_jitter):
    job = config_no_jitter.jobs[0]
    policy = JitterPolicy.from_dict(job.extra.get("jitter", {}))
    assert policy.max_seconds == 0.0
    assert policy.is_active is False


def test_second_job_has_no_jitter(config_with_jitter):
    job = config_with_jitter.jobs[1]
    policy = JitterPolicy.from_dict(job.extra.get("jitter", {}))
    assert policy.is_active is False
