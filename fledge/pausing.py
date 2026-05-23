"""Pause/resume support for individual jobs.

Allows a job to be administratively paused so the scheduler skips it
until it is explicitly resumed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class PausePolicy:
    """Per-job pause configuration loaded from TOML."""

    paused: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "PausePolicy":
        return cls(paused=bool(data.get("paused", False)))


class PauseRegistry:
    """Tracks which jobs are currently paused.

    Paused state is persisted to a JSON file so it survives daemon restarts.
    """

    def __init__(self, path: str = "") -> None:
        self._path = path
        self._paused: Set[str] = self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> Set[str]:
        if self._path and os.path.exists(self._path):
            try:
                with open(self._path, "r") as fh:
                    data = json.load(fh)
                return set(data.get("paused", []))
            except (json.JSONDecodeError, OSError):
                pass
        return set()

    def _save(self) -> None:
        if not self._path:
            return
        with open(self._path, "w") as fh:
            json.dump({"paused": sorted(self._paused)}, fh)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def seed(self, job_name: str, policy: PausePolicy) -> None:
        """Seed initial paused state from config (only if not already tracked)."""
        if policy.paused and job_name not in self._paused:
            self._paused.add(job_name)
            self._save()

    def pause(self, job_name: str) -> None:
        self._paused.add(job_name)
        self._save()

    def resume(self, job_name: str) -> None:
        self._paused.discard(job_name)
        self._save()

    def is_paused(self, job_name: str) -> bool:
        return job_name in self._paused

    def all_paused(self) -> Set[str]:
        return set(self._paused)
