"""Tests verifying AuditLog path is wired through FledgeConfig."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from fledge.config import load_config


@pytest.fixture
def config_with_audit(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""\
        [daemon]
        interval = 10

        [audit]
        path = "/var/log/fledge/audit.jsonl"

        [[jobs]]
        name = "example"
        command = "echo hi"
        schedule = "@every 60"
        """)
    )
    return cfg


@pytest.fixture
def config_no_audit(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""\
        [daemon]
        interval = 10

        [[jobs]]
        name = "example"
        command = "echo hi"
        schedule = "@every 60"
        """)
    )
    return cfg


def test_audit_path_parsed(config_with_audit):
    config = load_config(str(config_with_audit))
    assert config.audit_path == "/var/log/fledge/audit.jsonl"


def test_audit_path_defaults_when_section_absent(config_no_audit):
    config = load_config(str(config_no_audit))
    assert config.audit_path == "fledge_audit.jsonl"


def test_audit_path_is_string(config_with_audit):
    config = load_config(str(config_with_audit))
    assert isinstance(config.audit_path, str)
