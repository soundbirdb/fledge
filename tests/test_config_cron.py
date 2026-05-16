"""Tests for cron expression config parsing within FledgeConfig."""

import textwrap
import pytest
import tomllib

from fledge.config import load_config


@pytest.fixture
def config_with_cron(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval = 60

        [[jobs]]
        name = "cron_job"
        command = "echo cron"
        cron = "0 6 * * *"

        [[jobs]]
        name = "plain_job"
        command = "echo plain"
        interval = 300
    """))
    return cfg


@pytest.fixture
def config_no_cron(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval = 60

        [[jobs]]
        name = "plain_job"
        command = "echo plain"
        interval = 300
    """))
    return cfg


def test_cron_expression_parsed(config_with_cron):
    config = load_config(config_with_cron)
    job = next(j for j in config.jobs if j.name == "cron_job")
    assert job.cron.enabled
    assert job.cron.expression == "0 6 * * *"


def test_cron_defaults_when_absent(config_no_cron):
    config = load_config(config_no_cron)
    job = config.jobs[0]
    assert not job.cron.enabled
    assert job.cron.expression is None


def test_second_job_has_no_cron(config_with_cron):
    config = load_config(config_with_cron)
    job = next(j for j in config.jobs if j.name == "plain_job")
    assert not job.cron.enabled


def test_cron_and_interval_can_coexist(config_with_cron):
    """A job may define both cron and interval; both should be accessible."""
    config = load_config(config_with_cron)
    cron_job = next(j for j in config.jobs if j.name == "cron_job")
    assert cron_job.cron.enabled
