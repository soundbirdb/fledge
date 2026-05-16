"""Tests for fledge.notifier."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fledge.notifier import Notifier, NotifierConfig
from fledge.runner import JobResult


def _result(success: bool = True, error: str | None = None) -> JobResult:
    return JobResult(
        job_name="test_job",
        success=success,
        output="some output",
        error=error,
        duration_seconds=1.23,
    )


@pytest.fixture()
def cfg() -> NotifierConfig:
    return NotifierConfig(
        enabled=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_address="fledge@example.com",
        to_addresses=["ops@example.com"],
        notify_on_failure=True,
        notify_on_success=False,
    )


def test_notifier_config_from_dict():
    data = {
        "enabled": True,
        "smtp_host": "mail.local",
        "smtp_port": 25,
        "from_address": "a@b.com",
        "to_addresses": ["x@y.com"],
        "notify_on_failure": True,
        "notify_on_success": True,
    }
    nc = NotifierConfig.from_dict(data)
    assert nc.enabled is True
    assert nc.smtp_host == "mail.local"
    assert nc.to_addresses == ["x@y.com"]
    assert nc.notify_on_success is True


def test_notifier_config_defaults():
    nc = NotifierConfig.from_dict({})
    assert nc.enabled is False
    assert nc.smtp_port == 25
    assert nc.notify_on_failure is True
    assert nc.notify_on_success is False


def test_notify_skips_when_disabled(cfg):
    cfg.enabled = False
    notifier = Notifier(cfg)
    with patch("smtplib.SMTP") as mock_smtp:
        notifier.notify(_result(success=False))
    mock_smtp.assert_not_called()


def test_notify_skips_success_when_not_configured(cfg):
    cfg.notify_on_success = False
    notifier = Notifier(cfg)
    with patch("smtplib.SMTP") as mock_smtp:
        notifier.notify(_result(success=True))
    mock_smtp.assert_not_called()


def test_notify_sends_on_failure(cfg):
    notifier = Notifier(cfg)
    mock_smtp_instance = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp_instance
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        notifier.notify(_result(success=False, error="boom"))
    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)


def test_notify_warns_when_no_recipients(cfg, caplog):
    cfg.to_addresses = []
    notifier = Notifier(cfg)
    with patch("smtplib.SMTP") as mock_smtp:
        notifier.notify(_result(success=False))
    mock_smtp.assert_not_called()
    assert "no to_addresses" in caplog.text


def test_notify_logs_smtp_error(cfg, caplog):
    notifier = Notifier(cfg)
    with patch("smtplib.SMTP", side_effect=OSError("connection refused")):
        notifier.notify(_result(success=False))
    assert "Failed to send notification" in caplog.text
