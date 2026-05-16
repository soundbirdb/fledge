"""Configuration loading for fledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import tomllib


@dataclass
class JobConfig:
    name: str
    command: str
    interval_seconds: int
    enabled: bool = True
    timeout_seconds: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "JobConfig":
        return cls(
            name=data["name"],
            command=data["command"],
            interval_seconds=int(data["interval_seconds"]),
            enabled=bool(data.get("enabled", True)),
            timeout_seconds=data.get("timeout_seconds"),
        )


@dataclass
class LoggingConfig:
    level: str = "INFO"
    log_file: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingConfig":
        return cls(
            level=data.get("level", "INFO"),
            log_file=data.get("log_file"),
            max_bytes=int(data.get("max_bytes", 10 * 1024 * 1024)),
            backup_count=int(data.get("backup_count", 3)),
        )


@dataclass
class FledgeConfig:
    tick_interval: float
    jobs: List[JobConfig] = field(default_factory=list)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "FledgeConfig":
        daemon_section = data.get("daemon", {})
        logging_section = data.get("logging", {})
        jobs_section = data.get("jobs", [])
        return cls(
            tick_interval=float(daemon_section.get("tick_interval", 1.0)),
            jobs=[JobConfig.from_dict(j) for j in jobs_section],
            logging=LoggingConfig.from_dict(logging_section),
        )


def load_config(path: str | Path) -> FledgeConfig:
    """Load and parse a TOML configuration file."""
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    return FledgeConfig.from_dict(raw)
