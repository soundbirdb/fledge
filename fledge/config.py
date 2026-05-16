"""Configuration loading for fledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore

from fledge.notifier import NotifierConfig
from fledge.retry import RetryPolicy
from fledge.throttle import ThrottlePolicy
from fledge.circuit_breaker import CircuitBreakerPolicy


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingConfig":
        return cls(
            level=data.get("level", "INFO").upper(),
            file=data.get("file"),
        )


@dataclass
class DaemonConfig:
    interval: int = 60

    @classmethod
    def from_dict(cls, data: dict) -> "DaemonConfig":
        return cls(interval=int(data.get("interval", 60)))


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: str
    timeout: int = 300
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    throttle: ThrottlePolicy = field(default_factory=ThrottlePolicy)

    @classmethod
    def from_dict(cls, data: dict) -> "JobConfig":
        return cls(
            name=data["name"],
            command=data["command"],
            schedule=data["schedule"],
            timeout=int(data.get("timeout", 300)),
            retry=RetryPolicy.from_dict(data.get("retry", {})),
            throttle=ThrottlePolicy.from_dict(data.get("throttle", {})),
        )


@dataclass
class FledgeConfig:
    daemon: DaemonConfig
    jobs: List[JobConfig]
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    notifier: NotifierConfig = field(default_factory=NotifierConfig)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    throttle: ThrottlePolicy = field(default_factory=ThrottlePolicy)
    circuit_breaker: CircuitBreakerPolicy = field(default_factory=CircuitBreakerPolicy)


def load_config(path: str) -> FledgeConfig:
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)

    daemon = DaemonConfig.from_dict(raw.get("daemon", {}))
    jobs = [JobConfig.from_dict(j) for j in raw.get("jobs", [])]
    logging_cfg = LoggingConfig.from_dict(raw.get("logging", {}))
    notifier = NotifierConfig.from_dict(raw.get("notifier", {}))
    retry = RetryPolicy.from_dict(raw.get("retry", {}))
    throttle = ThrottlePolicy.from_dict(raw.get("throttle", {}))
    circuit_breaker = CircuitBreakerPolicy.from_dict(raw.get("circuit_breaker", {}))

    return FledgeConfig(
        daemon=daemon,
        jobs=jobs,
        logging=logging_cfg,
        notifier=notifier,
        retry=retry,
        throttle=throttle,
        circuit_breaker=circuit_breaker,
    )
