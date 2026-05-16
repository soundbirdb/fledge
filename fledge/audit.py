"""Audit log: records every job execution event to a structured JSONL file."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fledge.runner import JobResult


@dataclass
class AuditEntry:
    job_name: str
    started_at: str
    finished_at: str
    success: bool
    exit_code: Optional[int]
    duration: float
    attempt: int = 1
    error: Optional[str] = None

    @classmethod
    def from_result(cls, result: JobResult, attempt: int = 1) -> "AuditEntry":
        return cls(
            job_name=result.job_name,
            started_at=result.started_at.isoformat(),
            finished_at=result.finished_at.isoformat(),
            success=result.success,
            exit_code=result.exit_code,
            duration=result.duration,
            attempt=attempt,
            error=result.error,
        )

    def as_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "success": self.success,
            "exit_code": self.exit_code,
            "duration": self.duration,
            "attempt": self.attempt,
            "error": self.error,
        }


class AuditLog:
    """Thread-safe append-only audit log backed by a JSONL file."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, result: JobResult, attempt: int = 1) -> AuditEntry:
        entry = AuditEntry.from_result(result, attempt=attempt)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry.as_dict()) + "\n")
        return entry

    def read_all(self) -> list[AuditEntry]:
        if not self._path.exists():
            return []
        entries: list[AuditEntry] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(AuditEntry(**data))
        return entries
