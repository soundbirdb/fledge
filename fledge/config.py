"""Configuration loading for fledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]

from fledge.notifier import NotifierConfig


@dataclass
class JobConfig:
    name: str
    command: str
    interval_seconds: int
    timeout_seconds: int = 60
    enabled: bool = True

    @staticmethod
    def from_dict(data: dict) -> "JobConfig":
        return JobConfig(
            name=data["name"],
            command=data["command"],
            interval_seconds=int(data["interval_seconds"]),
            timeout_seconds=int(data.get("timeout_seconds", 60)),
            enabled=data.get("enabled", True),
        )


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> "LoggingConfig":
        return LoggingConfig(
            level=data.get("level", "INFO").upper(),
            file=data.get("file"),
        )


@dataclass
class DaemonConfig:
    tick_seconds: int = 10
    history_file: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> "DaemonConfig":
        return DaemonConfig(
            tick_seconds=int(data.get("tick_seconds", 10)),
            history_file=data.get("history_file"),
        )


@dataclass
class FledgeConfig:
    daemon: DaemonConfig
    jobs: List[JobConfig]
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    notifier: NotifierConfig = field(default_factory=NotifierConfig)


def load_config(path: Path) -> FledgeConfig:
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)

    daemon = DaemonConfig.from_dict(raw.get("daemon", {}))
    jobs = [JobConfig.from_dict(j) for j in raw.get("jobs", [])]
    logging_cfg = LoggingConfig.from_dict(raw.get("logging", {}))
    notifier_cfg = NotifierConfig.from_dict(raw.get("notifier", {}))

    return FledgeConfig(
        daemon=daemon,
        jobs=jobs,
        logging=logging_cfg,
        notifier=notifier_cfg,
    )
