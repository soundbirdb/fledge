"""Integration tests: skip policy parsed from a full TOML config."""
from __future__ import annotations

import textwrap
import pytest

from fledge.config import FledgeConfig


@pytest.fixture
def config_with_skip(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""\
            [daemon]
            interval = 60

            [[jobs]]
            name = "ingest"
            command = "python ingest.py"
            every = 300

            [jobs.skip]
            env_var = "DISABLE_INGEST"
            env_value = "true"

            [[jobs]]
            name = "report"
            command = "python report.py"
            every = 600
        """)
    )
    return FledgeConfig.from_file(str(cfg))


@pytest.fixture
def config_no_skip(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""\
            [daemon]
            interval = 60

            [[jobs]]
            name = "ingest"
            command = "python ingest.py"
            every = 300
        """)
    )
    return FledgeConfig.from_file(str(cfg))


def test_skip_policy_parsed(config_with_skip):
    from fledge.skippolicy import SkipPolicy
    job = config_with_skip.jobs[0]
    policy = SkipPolicy.from_dict(job.options)
    assert policy.env_var == "DISABLE_INGEST"
    assert policy.env_value == "true"
    assert policy.always is False


def test_skip_defaults_when_section_absent(config_no_skip):
    from fledge.skippolicy import SkipPolicy
    job = config_no_skip.jobs[0]
    policy = SkipPolicy.from_dict(job.options)
    assert policy.env_var == ""
    assert policy.always is False
    assert policy.enabled is False


def test_second_job_has_no_skip(config_with_skip):
    from fledge.skippolicy import SkipPolicy
    job = config_with_skip.jobs[1]
    policy = SkipPolicy.from_dict(job.options)
    assert policy.enabled is False
