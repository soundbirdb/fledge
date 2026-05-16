"""Tests for LoggingConfig parsing within FledgeConfig."""

import textwrap
from pathlib import Path

import pytest

from fledge.config import FledgeConfig, LoggingConfig, load_config


@pytest.fixture
def config_with_logging(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        [daemon]
        tick_interval = 2.0

        [logging]
        level = "DEBUG"
        log_file = "/var/log/fledge.log"
        max_bytes = 5242880
        backup_count = 5

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        interval_seconds = 60
    """)
    p = tmp_path / "fledge.toml"
    p.write_text(content)
    return p


@pytest.fixture
def config_no_logging(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        [daemon]
        tick_interval = 1.0

        [[jobs]]
        name = "sync"
        command = "python sync.py"
        interval_seconds = 30
    """)
    p = tmp_path / "fledge_minimal.toml"
    p.write_text(content)
    return p


def test_logging_config_parsed(config_with_logging):
    cfg = load_config(config_with_logging)
    assert isinstance(cfg.logging, LoggingConfig)
    assert cfg.logging.level == "DEBUG"
    assert cfg.logging.log_file == "/var/log/fledge.log"
    assert cfg.logging.max_bytes == 5_242_880
    assert cfg.logging.backup_count == 5


def test_logging_config_defaults_when_section_absent(config_no_logging):
    cfg = load_config(config_no_logging)
    assert cfg.logging.level == "INFO"
    assert cfg.logging.log_file is None
    assert cfg.logging.max_bytes == 10 * 1024 * 1024
    assert cfg.logging.backup_count == 3


def test_logging_config_from_dict_partial():
    lc = LoggingConfig.from_dict({"level": "WARNING"})
    assert lc.level == "WARNING"
    assert lc.log_file is None


def test_fledge_config_has_logging_attribute():
    cfg = FledgeConfig.from_dict({"daemon": {"tick_interval": 1.0}, "jobs": []})
    assert hasattr(cfg, "logging")
    assert isinstance(cfg.logging, LoggingConfig)
