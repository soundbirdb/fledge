"""Webhook notification support for job results."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

from fledge.logging_config import get_logger

log = get_logger(__name__)


@dataclass
class WebhookConfig:
    url: str = ""
    enabled: bool = True
    timeout_seconds: int = 5
    on_failure_only: bool = False
    headers: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "WebhookConfig":
        return cls(
            url=data.get("url", ""),
            enabled=data.get("enabled", True),
            timeout_seconds=int(data.get("timeout_seconds", 5)),
            on_failure_only=data.get("on_failure_only", False),
            headers=data.get("headers", {}),
        )


class WebhookNotifier:
    """Sends HTTP POST payloads to a configured webhook URL on job completion."""

    def __init__(self, config: WebhookConfig) -> None:
        self._cfg = config

    def notify(self, result) -> None:
        cfg = self._cfg
        if not cfg.enabled or not cfg.url:
            return
        if cfg.on_failure_only and result.success:
            return

        payload = json.dumps({
            "job": result.job_name,
            "success": result.success,
            "duration": result.duration,
            "error": str(result.error) if result.error else None,
        }).encode()

        headers = {"Content-Type": "application/json", **cfg.headers}
        req = urllib.request.Request(cfg.url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=cfg.timeout_seconds):
                log.debug("Webhook delivered for job '%s'", result.job_name)
        except urllib.error.URLError as exc:
            log.warning("Webhook delivery failed for job '%s': %s", result.job_name, exc)
        except Exception as exc:  # noqa: BLE001
            log.warning("Webhook unexpected error for job '%s': %s", result.job_name, exc)
