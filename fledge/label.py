"""Job labelling — attach arbitrary key/value metadata to jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LabelPolicy:
    labels: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "LabelPolicy":
        raw = data.get("labels", {})
        if isinstance(raw, str):
            # Support comma-separated "key=value" pairs as a convenience
            parsed: Dict[str, str] = {}
            for pair in raw.split(","):
                pair = pair.strip()
                if "=" in pair:
                    k, _, v = pair.partition("=")
                    parsed[k.strip()] = v.strip()
            return cls(labels=parsed)
        if isinstance(raw, dict):
            return cls(labels={str(k): str(v) for k, v in raw.items()})
        return cls()

    def enabled(self) -> bool:
        return bool(self.labels)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.labels.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.labels

    def matches(self, key: str, value: str) -> bool:
        return self.labels.get(key) == value


class LabelRegistry:
    """Maps job names to their LabelPolicy instances."""

    def __init__(self) -> None:
        self._registry: Dict[str, LabelPolicy] = {}

    def register(self, job_name: str, policy: LabelPolicy) -> None:
        self._registry[job_name] = policy

    def get(self, job_name: str) -> LabelPolicy:
        return self._registry.get(job_name, LabelPolicy())

    def jobs_with_label(self, key: str, value: Optional[str] = None) -> list:
        """Return job names that carry *key* (optionally matching *value*)."""
        results = []
        for name, policy in self._registry.items():
            if policy.has(key):
                if value is None or policy.matches(key, value):
                    results.append(name)
        return sorted(results)

    def all_labels(self) -> Dict[str, Dict[str, str]]:
        """Return a mapping of job_name -> labels dict for all registered jobs."""
        return {name: dict(p.labels) for name, p in self._registry.items() if p.enabled()}
