"""TOML configuration loader for fledge job queue daemon."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "tomllib (Python 3.11+) or tomli package is required. "
            "Install with: pip install tomli"
        )


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: str
    enabled: bool = True
    timeout: int = 300
    env: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "JobConfig":
        return cls(
            name=name,
            command=data["command"],
            schedule=data["schedule"],
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 300),
            env=data.get("env", {}),
        )


@dataclass
class FledgeConfig:
    log_level: str = "INFO"
    log_file: str | None = None
    jobs: list[JobConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FledgeConfig":
        daemon_section = data.get("daemon", {})
        jobs_section = data.get("jobs", {})

        jobs = [
            JobConfig.from_dict(name, job_data)
            for name, job_data in jobs_section.items()
        ]

        return cls(
            log_level=daemon_section.get("log_level", "INFO"),
            log_file=daemon_section.get("log_file"),
            jobs=jobs,
        )


def load_config(path: str | Path) -> FledgeConfig:
    """Load and parse a fledge TOML configuration file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    if not config_path.is_file():
        raise ValueError(f"Config path is not a file: {config_path}")

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    return FledgeConfig.from_dict(raw)
