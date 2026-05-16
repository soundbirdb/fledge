"""Snapshot: captures and persists the last known state of each job."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

from fledge.runner import JobResult


@dataclass
class JobSnapshot:
    job_name: str
    last_status: str          # "success" | "failure"
    last_run_at: float        # unix timestamp
    last_duration: float      # seconds
    last_error: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_result(cls, result: JobResult) -> "JobSnapshot":
        return cls(
            job_name=result.job_name,
            last_status="success" if result.success else "failure",
            last_run_at=result.finished_at,
            last_duration=result.duration,
            last_error=result.error,
        )


class SnapshotStore:
    """Persists the most recent JobSnapshot for every job to a JSON file."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._snapshots: Dict[str, JobSnapshot] = {}
        self._load()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def update(self, result: JobResult) -> None:
        """Record the latest result for a job, then flush to disk."""
        snap = JobSnapshot.from_result(result)
        self._snapshots[snap.job_name] = snap
        self._flush()

    def get(self, job_name: str) -> Optional[JobSnapshot]:
        return self._snapshots.get(job_name)

    def all(self) -> Dict[str, JobSnapshot]:
        return dict(self._snapshots)

    # ------------------------------------------------------------------
    # private helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw: dict = json.loads(self._path.read_text())
            for name, entry in raw.items():
                self._snapshots[name] = JobSnapshot(**entry)
        except (json.JSONDecodeError, TypeError):
            self._snapshots = {}

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {name: snap.as_dict() for name, snap in self._snapshots.items()}
        self._path.write_text(json.dumps(payload, indent=2))
