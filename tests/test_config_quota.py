"""Tests that quota settings are parsed correctly from a TOML config."""

import textwrap
import pytest
from fledge.config import load_config
from fledge.quota import QuotaPolicy


@pytest.fixture
def config_with_quota(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "capped_job"
        command = "echo hi"
        every = 60

        [jobs.quota]
        max_runs = 10
        window_seconds = 3600

        [[jobs]]
        name = "unlimited_job"
        command = "echo bye"
        every = 120
    """))
    return cfg


@pytest.fixture
def config_no_quota(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "plain_job"
        command = "echo plain"
        every = 30
    """))
    return cfg


def test_quota_policy_parsed(config_with_quota):
    config = load_config(config_with_quota)
    job = config.jobs[0]
    assert job.name == "capped_job"
    policy = QuotaPolicy.from_dict(job.quota)
    assert policy.max_runs == 10
    assert policy.window_seconds == 3600
    assert policy.enabled


def test_quota_defaults_when_section_absent(config_with_quota):
    config = load_config(config_with_quota)
    job = config.jobs[1]
    assert job.name == "unlimited_job"
    policy = QuotaPolicy.from_dict(job.quota)
    assert not policy.enabled


def test_quota_defaults_when_no_quota_key(config_no_quota):
    config = load_config(config_no_quota)
    job = config.jobs[0]
    policy = QuotaPolicy.from_dict(job.quota)
    assert policy.max_runs == 0
    assert not policy.enabled


def test_quota_from_dict_partial(config_with_quota):
    policy = QuotaPolicy.from_dict({"max_runs": 5})
    assert policy.max_runs == 5
    assert policy.window_seconds == 3600
