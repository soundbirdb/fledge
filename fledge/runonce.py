"""Run-once policy: ensure a job only executes once per calendar day (or ever)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Optional


@dataclass
class RunOncePolicy:
    enabled: bool = False
    scope: str = "day"  # "day" | "forever"

    @classmethod
    def from_dict(cls, data: dict) -> "RunOncePolicy":
        raw = data.get("run_once", {})
        if not raw:
            return cls()
        return cls(
            enabled=bool(raw.get("enabled", False)),
            scope=str(raw.get("scope", "day")),
        )


class RunOnceTracker:
    """Persists run-once state to a JSON file."""

    def __init__(self, path: str = ".fledge_runonce.json") -> None:
        self._path = path
        self._state: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if os.path.exists(self._path):
            try:
                with open(self._path) as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump(self._state, fh)

    def has_run(self, job_name: str, scope: str) -> bool:
        if job_name not in self._state:
            return False
        if scope == "forever":
            return True
        # scope == "day"
        last = self._state[job_name]
        return last == date.today().isoformat()

    def record(self, job_name: str) -> None:
        self._state[job_name] = date.today().isoformat()
        self._save()

    def reset(self, job_name: Optional[str] = None) -> None:
        if job_name is None:
            self._state.clear()
        else:
            self._state.pop(job_name, None)
        self._save()
