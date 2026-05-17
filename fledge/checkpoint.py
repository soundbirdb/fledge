"""Checkpoint support — persist and restore a job's last successful run cursor."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CheckpointPolicy:
    enabled: bool = False
    path: str = "fledge_checkpoints.json"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointPolicy":
        raw = data.get("checkpoint", {})
        if not raw:
            return cls()
        return cls(
            enabled=bool(raw.get("enabled", False)),
            path=str(raw.get("path", "fledge_checkpoints.json")),
        )


class CheckpointStore:
    """Persist per-job cursor values to a JSON file."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._data: Dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as fh:
                    self._data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    # ------------------------------------------------------------------
    def get(self, job_name: str) -> Optional[Any]:
        """Return the stored cursor for *job_name*, or None."""
        return self._data.get(job_name)

    def set(self, job_name: str, cursor: Any) -> None:
        """Persist *cursor* for *job_name*."""
        self._data[job_name] = cursor
        self._save()

    def clear(self, job_name: str) -> None:
        """Remove the checkpoint for *job_name* if it exists."""
        if job_name in self._data:
            del self._data[job_name]
            self._save()

    def all(self) -> Dict[str, Any]:
        """Return a shallow copy of all stored checkpoints."""
        return dict(self._data)
