"""Tests for notifier section parsing in FledgeConfig."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from fledge.config import load_config
from fledge.notifier import NotifierConfig


@pytest.fixture()
def config_with_notifier(tmp_path: Path) -> Path:
    content = textwrap.dedent("""
        [daemon]
        tick_seconds = 5

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        interval_seconds = 300

        [notifier]
        enabled = true
        smtp_host = "mail.example.com"
        smtp_port = 587
        from_address = "fledge@example.com"
        to_addresses = ["ops@example.com", "dev@example.com"]
        notify_on_failure = true
        notify_on_success = false
    """)
    p = tmp_path / "fledge.toml"
    p.write_text(content)
    return p


@pytest.fixture()
def config_no_notifier(tmp_path: Path) -> Path:
    content = textwrap.dedent("""
        [daemon]
        tick_seconds = 5

        [[jobs]]
        name = "ingest"
        command = "python ingest.py"
        interval_seconds = 300
    """)
    p = tmp_path / "fledge.toml"
    p.write_text(content)
    return p


def test_notifier_config_parsed(config_with_notifier):
    cfg = load_config(config_with_notifier)
    assert isinstance(cfg.notifier, NotifierConfig)
    assert cfg.notifier.enabled is True
    assert cfg.notifier.smtp_host == "mail.example.com"
    assert cfg.notifier.smtp_port == 587
    assert cfg.notifier.from_address == "fledge@example.com"
    assert cfg.notifier.to_addresses == ["ops@example.com", "dev@example.com"]
    assert cfg.notifier.notify_on_failure is True
    assert cfg.notifier.notify_on_success is False


def test_notifier_defaults_when_section_absent(config_no_notifier):
    cfg = load_config(config_no_notifier)
    assert isinstance(cfg.notifier, NotifierConfig)
    assert cfg.notifier.enabled is False
    assert cfg.notifier.smtp_host == "localhost"
    assert cfg.notifier.to_addresses == []


def test_notifier_config_from_dict_partial():
    nc = NotifierConfig.from_dict({"enabled": True, "to_addresses": ["a@b.com"]})
    assert nc.enabled is True
    assert nc.smtp_host == "localhost"
    assert nc.smtp_port == 25
    assert nc.to_addresses == ["a@b.com"]
