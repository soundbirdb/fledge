"""Tests for fledge TOML configuration loader."""

import pytest
from pathlib import Path
from textwrap import dedent

from fledge.config import FledgeConfig, JobConfig, load_config


SAMPLE_TOML = dedent("""\
    [daemon]
    log_level = "DEBUG"
    log_file = "/var/log/fledge.log"

    [jobs.ingest_sales]
    command = "python scripts/ingest_sales.py"
    schedule = "0 * * * *"
    timeout = 120

    [jobs.sync_inventory]
    command = "python scripts/sync_inventory.py"
    schedule = "*/15 * * * *"
    enabled = false
    env = { DB_HOST = "localhost", DB_PORT = "5432" }
""")


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(SAMPLE_TOML)
    return cfg


def test_load_config_returns_fledge_config(config_file):
    config = load_config(config_file)
    assert isinstance(config, FledgeConfig)


def test_daemon_section_parsed(config_file):
    config = load_config(config_file)
    assert config.log_level == "DEBUG"
    assert config.log_file == "/var/log/fledge.log"


def test_jobs_count(config_file):
    config = load_config(config_file)
    assert len(config.jobs) == 2


def test_job_fields_parsed(config_file):
    config = load_config(config_file)
    job = next(j for j in config.jobs if j.name == "ingest_sales")
    assert job.command == "python scripts/ingest_sales.py"
    assert job.schedule == "0 * * * *"
    assert job.timeout == 120
    assert job.enabled is True


def test_job_disabled_and_env(config_file):
    config = load_config(config_file)
    job = next(j for j in config.jobs if j.name == "sync_inventory")
    assert job.enabled is False
    assert job.env == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_defaults_when_daemon_section_missing(tmp_path):
    cfg = tmp_path / "minimal.toml"
    cfg.write_text('[jobs.ping]\ncommand = "echo hi"\nschedule = "* * * * *"\n')
    config = load_config(cfg)
    assert config.log_level == "INFO"
    assert config.log_file is None


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/fledge.toml")


def test_directory_path_raises(tmp_path):
    with pytest.raises(ValueError):
        load_config(tmp_path)
