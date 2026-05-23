"""Tests for pause policy parsed from a full FledgeConfig TOML."""

from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config
from fledge.pausing import PausePolicy


TOML_WITH_PAUSE = textwrap.dedent("""
    [daemon]
    interval = 10

    [[jobs]]
    name = "ingest_a"
    command = "python ingest_a.py"
    every = 60

    [jobs.pause]
    paused = true

    [[jobs]]
    name = "ingest_b"
    command = "python ingest_b.py"
    every = 120
""")

TOML_NO_PAUSE = textwrap.dedent("""
    [daemon]
    interval = 10

    [[jobs]]
    name = "ingest_a"
    command = "python ingest_a.py"
    every = 60
""")


@pytest.fixture
def config_with_pause(tmp_path):
    p = tmp_path / "fledge.toml"
    p.write_text(TOML_WITH_PAUSE)
    return load_config(str(p))


@pytest.fixture
def config_no_pause(tmp_path):
    p = tmp_path / "fledge.toml"
    p.write_text(TOML_NO_PAUSE)
    return load_config(str(p))


def test_pause_policy_parsed(config_with_pause):
    job = config_with_pause.jobs[0]
    assert job.pause.paused is True


def test_pause_defaults_when_section_absent(config_with_pause):
    job = config_with_pause.jobs[1]
    assert job.pause.paused is False


def test_pause_defaults_when_no_pause_key(config_no_pause):
    job = config_no_pause.jobs[0]
    assert job.pause.paused is False


def test_pause_policy_is_pause_policy_instance(config_with_pause):
    job = config_with_pause.jobs[0]
    assert isinstance(job.pause, PausePolicy)
