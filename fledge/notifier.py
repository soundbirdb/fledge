"""Job result notification support for fledge."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import List, Optional

from fledge.logging_config import get_logger
from fledge.runner import JobResult

logger = get_logger(__name__)


@dataclass
class NotifierConfig:
    enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 25
    from_address: str = "fledge@localhost"
    to_addresses: List[str] = field(default_factory=list)
    notify_on_failure: bool = True
    notify_on_success: bool = False

    @staticmethod
    def from_dict(data: dict) -> "NotifierConfig":
        return NotifierConfig(
            enabled=data.get("enabled", False),
            smtp_host=data.get("smtp_host", "localhost"),
            smtp_port=int(data.get("smtp_port", 25)),
            from_address=data.get("from_address", "fledge@localhost"),
            to_addresses=data.get("to_addresses", []),
            notify_on_failure=data.get("notify_on_failure", True),
            notify_on_success=data.get("notify_on_success", False),
        )


class Notifier:
    """Sends email notifications for job results."""

    def __init__(self, config: NotifierConfig) -> None:
        self._config = config

    def notify(self, result: JobResult) -> None:
        """Send a notification for *result* if configured to do so."""
        if not self._config.enabled:
            return
        if result.success and not self._config.notify_on_success:
            return
        if not result.success and not self._config.notify_on_failure:
            return
        if not self._config.to_addresses:
            logger.warning("Notifier enabled but no to_addresses configured")
            return
        self._send(result)

    def _send(self, result: JobResult) -> None:
        status = "succeeded" if result.success else "failed"
        subject = f"[fledge] Job '{result.job_name}' {status}"
        body_lines = [
            f"Job: {result.job_name}",
            f"Status: {status}",
            f"Duration: {result.duration_seconds:.2f}s",
        ]
        if result.error:
            body_lines.append(f"Error: {result.error}")
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._config.from_address
        msg["To"] = ", ".join(self._config.to_addresses)
        msg.set_content("\n".join(body_lines))
        try:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as smtp:
                smtp.send_message(msg)
            logger.info("Notification sent for job '%s'", result.job_name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send notification: %s", exc)
