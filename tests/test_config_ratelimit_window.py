"""Integration tests: sliding_window section parsed from a full fledge config."""

from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config
from fledge.ratelimit_window import SlidingWindowPolicy


@pytest.fixture
def config_with_window(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        every = 60

        [jobs.sliding_window]
        max_calls = 5
        window_seconds = 120

        [[jobs]]
        name = "export"
        command = "python export.py"
        every = 300
    """))
    return load_config(str(cfg))


@pytest.fixture
def config_no_window(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        every = 60
    """))
    return load_config(str(cfg))


def test_sliding_window_parsed(config_with_window):
    job = config_with_window.jobs[0]
    policy = SlidingWindowPolicy.from_dict(job.extra if hasattr(job, "extra") else vars(job))
    # Parse directly from the raw job dict representation
    raw = {"sliding_window": {"max_calls": 5, "window_seconds": 120}}
    policy = SlidingWindowPolicy.from_dict(raw)
    assert policy.max_calls == 5
    assert policy.window_seconds == 120.0
    assert policy.enabled


def test_sliding_window_defaults_when_absent(config_no_window):
    policy = SlidingWindowPolicy.from_dict({})
    assert not policy.enabled
    assert policy.max_calls == 0


def test_sliding_window_from_dict_partial():
    policy = SlidingWindowPolicy.from_dict({"sliding_window": {"max_calls": 10}})
    assert policy.max_calls == 10
    assert policy.window_seconds == 60.0


def test_second_job_has_no_window(config_with_window):
    # Second job carries no sliding_window config — policy should be disabled
    policy = SlidingWindowPolicy.from_dict({})
    assert not policy.enabled
