"""Tests verifying retry policy is parsed from job config TOML sections."""

import textwrap
import pytest
from pathlib import Path
from fledge.config import load_config
from fledge.retry import RetryPolicy


@pytest.fixture
def config_with_retry(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        [daemon]
        tick_seconds = 5

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        interval_seconds = 60

        [jobs.retry]
        max_attempts = 4
        delay_seconds = 3.0
        backoff_factor = 2.0

        [[jobs]]
        name = "export"
        command = "python export.py"
        interval_seconds = 120
    """)
    p = tmp_path / "fledge.toml"
    p.write_text(content)
    return p


@pytest.fixture
def config_no_retry(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        [[jobs]]
        name = "simple"
        command = "echo hi"
        interval_seconds = 30
    """)
    p = tmp_path / "fledge.toml"
    p.write_text(content)
    return p


def test_retry_policy_parsed(config_with_retry):
    cfg = load_config(config_with_retry)
    job = cfg.jobs[0]
    assert job.name == "ingest"
    assert isinstance(job.retry, RetryPolicy)
    assert job.retry.max_attempts == 4
    assert job.retry.delay_seconds == 3.0
    assert job.retry.backoff_factor == 2.0


def test_retry_defaults_when_section_absent(config_with_retry):
    cfg = load_config(config_with_retry)
    job = cfg.jobs[1]  # export job has no [retry] section
    assert job.retry.max_attempts == 1
    assert job.retry.delay_seconds == 5.0
    assert job.retry.backoff_factor == 1.0


def test_retry_defaults_no_retry_key(config_no_retry):
    cfg = load_config(config_no_retry)
    job = cfg.jobs[0]
    assert isinstance(job.retry, RetryPolicy)
    assert job.retry.max_attempts == 1


def test_retry_policy_from_dict_partial():
    p = RetryPolicy.from_dict({"max_attempts": 2})
    assert p.max_attempts == 2
    assert p.delay_seconds == 5.0
    assert p.backoff_factor == 1.0


def test_retry_policy_from_dict_empty():
    p = RetryPolicy.from_dict({})
    assert p.max_attempts == 1
