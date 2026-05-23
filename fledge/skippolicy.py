"""Skip policy — allows a job to be conditionally skipped based on
an environment variable or a callable predicate."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class SkipPolicy:
    """Configuration for conditional job skipping."""

    # Skip when this env-var is set to a truthy value ("1", "true", "yes").
    env_var: str = ""
    # Skip when this env-var equals a specific value.
    env_value: str = ""
    # Always skip (static flag, useful for temporarily disabling a job).
    always: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "SkipPolicy":
        skip = data.get("skip", {})
        if not isinstance(skip, dict):
            return cls()
        return cls(
            env_var=str(skip.get("env_var", "")),
            env_value=str(skip.get("env_value", "")),
            always=bool(skip.get("always", False)),
        )

    @property
    def enabled(self) -> bool:
        return bool(self.env_var or self.always)


class SkipEvaluator:
    """Decides whether a job should be skipped for the current run."""

    def __init__(
        self,
        policy: SkipPolicy,
        predicate: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._policy = policy
        self._predicate = predicate

    def should_skip(self) -> bool:
        """Return True if the job should be skipped."""
        if self._policy.always:
            return True

        if self._predicate is not None and self._predicate():
            return True

        if self._policy.env_var:
            raw = os.environ.get(self._policy.env_var, "")
            if self._policy.env_value:
                return raw == self._policy.env_value
            return raw.lower() in ("1", "true", "yes")

        return False
