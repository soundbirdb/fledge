"""Integration tests: run_once parsed from a full TOML config."""
from __future__ import annotations

import textwrap
import pytest

from fledge.config import load_config
from fledge.runonce import RunOncePolicy


@pytest.fixture
def config_with_runonce(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval = 60

        [[jobs]]
        name = "daily_ingest"
        command = "python ingest.py"
        every = 3600

        [jobs.run_once]
        enabled = true
        scope = "day"

        [[jobs]]
        name = "one_time_setup"
        command = "python setup.py"
        every = 0

        [jobs.run_once]
        enabled = true
        scope = "forever"
    """))
    return load_config(str(cfg))


@pytest.fixture
def config_no_runonce(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval = 60

        [[jobs]]
        name = "plain_job"
        command = "echo hi"
        every = 300
    """))
    return load_config(str(cfg))


def test_runonce_policy_parsed(config_with_runonce):
    job = config_with_runonce.jobs[0]
    p = RunOncePolicy.from_dict(job.extra)
    assert p.enabled is True
    assert p.scope == "day"


def test_runonce_forever_scope(config_with_runonce):
    job = config_with_runonce.jobs[1]
    p = RunOncePolicy.from_dict(job.extra)
    assert p.enabled is True
    assert p.scope == "forever"


def test_runonce_defaults_when_absent(config_no_runonce):
    job = config_no_runonce.jobs[0]
    p = RunOncePolicy.from_dict(job.extra)
    assert p.enabled is False
    assert p.scope == "day"
