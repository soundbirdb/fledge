"""Tests for fledge.webhook."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from fledge.webhook import WebhookConfig, WebhookNotifier


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, job_name="test_job", success=True, duration=1.2, error=None):
        self.job_name = job_name
        self.success = success
        self.duration = duration
        self.error = error


@pytest.fixture()
def cfg():
    return WebhookConfig(url="http://example.com/hook", enabled=True)


# ---------------------------------------------------------------------------
# WebhookConfig
# ---------------------------------------------------------------------------

class TestWebhookConfig:
    def test_defaults(self):
        c = WebhookConfig()
        assert c.url == ""
        assert c.enabled is True
        assert c.timeout_seconds == 5
        assert c.on_failure_only is False
        assert c.headers == {}

    def test_from_dict_full(self):
        c = WebhookConfig.from_dict({
            "url": "http://x.io/hook",
            "enabled": False,
            "timeout_seconds": 10,
            "on_failure_only": True,
            "headers": {"X-Token": "abc"},
        })
        assert c.url == "http://x.io/hook"
        assert c.enabled is False
        assert c.timeout_seconds == 10
        assert c.on_failure_only is True
        assert c.headers == {"X-Token": "abc"}

    def test_from_dict_empty(self):
        c = WebhookConfig.from_dict({})
        assert c.url == ""
        assert c.enabled is True


# ---------------------------------------------------------------------------
# WebhookNotifier
# ---------------------------------------------------------------------------

class TestWebhookNotifier:
    def test_skips_when_disabled(self, cfg):
        cfg.enabled = False
        notifier = WebhookNotifier(cfg)
        with patch("urllib.request.urlopen") as mock_open:
            notifier.notify(_FakeResult())
            mock_open.assert_not_called()

    def test_skips_when_no_url(self):
        notifier = WebhookNotifier(WebhookConfig(url=""))
        with patch("urllib.request.urlopen") as mock_open:
            notifier.notify(_FakeResult())
            mock_open.assert_not_called()

    def test_skips_success_when_on_failure_only(self, cfg):
        cfg.on_failure_only = True
        notifier = WebhookNotifier(cfg)
        with patch("urllib.request.urlopen") as mock_open:
            notifier.notify(_FakeResult(success=True))
            mock_open.assert_not_called()

    def test_sends_on_failure_when_on_failure_only(self, cfg):
        cfg.on_failure_only = True
        notifier = WebhookNotifier(cfg)
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=MagicMock())
        cm.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=cm) as mock_open:
            notifier.notify(_FakeResult(success=False, error=RuntimeError("boom")))
            mock_open.assert_called_once()

    def test_payload_contains_job_fields(self, cfg):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["data"] = json.loads(req.data)
            cm = MagicMock()
            cm.__enter__ = MagicMock(return_value=MagicMock())
            cm.__exit__ = MagicMock(return_value=False)
            return cm

        notifier = WebhookNotifier(cfg)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            notifier.notify(_FakeResult(job_name="ingest", success=True, duration=2.5))

        assert captured["data"]["job"] == "ingest"
        assert captured["data"]["success"] is True
        assert captured["data"]["duration"] == 2.5
        assert captured["data"]["error"] is None

    def test_url_error_does_not_raise(self, cfg):
        import urllib.error
        notifier = WebhookNotifier(cfg)
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            notifier.notify(_FakeResult())  # should not raise
