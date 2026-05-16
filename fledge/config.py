"""Configuration loading and dataclasses for fledge."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from fledge.retry import RetryPolicy


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingConfig":
        return cls(
            level=data.get("level", "INFO").upper(),
            file=data.get("file"),
        )


@dataclass
class NotifierConfig:
    enabled: bool = False
    webhook_url: Optional[str] = None
    on_failure_only: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "NotifierConfig":
        return cls(
            enabled=bool(data.get("enabled", False)),
            webhook_url=data.get("webhook_url"),
            on_failure_only=bool(data.get("on_failure_only", True)),
        )


@dataclass
class JobConfig:
    name: str
    command: str
    interval_seconds: int
    enabled: bool = True
    timeout_seconds: Optional[int] = None
    retry: RetryPolicy = field(default_factory=RetryPolicy)

    @classmethod
    def from_dict(cls, data: dict) -> "JobConfig":
        return cls(
            name=data["name"],
            command=data["command"],
            interval_seconds=int(data["interval_seconds"]),
            enabled=bool(data.get("enabled", True)),
            timeout_seconds=(
                int(data["timeout_seconds"]) if "timeout_seconds" in data else None
            ),
            retry=RetryPolicy.from_dict(data.get("retry", {})),
        )


@dataclass
class DaemonConfig:
    tick_seconds: int = 10
    history_file: Optional[str] = None
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    notifier: NotifierConfig = field(default_factory=NotifierConfig)
    jobs: List[JobConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "DaemonConfig":
        daemon_section = data.get("daemon", {})
        logging_section = data.get("logging", {})
        notifier_section = data.get("notifier", {})
        jobs_section = data.get("jobs", [])
        return cls(
            tick_seconds=int(daemon_section.get("tick_seconds", 10)),
            history_file=daemon_section.get("history_file"),
            logging=LoggingConfig.from_dict(logging_section),
            notifier=NotifierConfig.from_dict(notifier_section),
            jobs=[JobConfig.from_dict(j) for j in jobs_section],
        )


def load_config(path: str | Path) -> DaemonConfig:
    """Load and parse a TOML configuration file."""
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    return DaemonConfig.from_dict(raw)
