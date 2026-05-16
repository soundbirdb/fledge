"""Job run history tracking for fledge."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class HistoryEntry:
    job_name: str
    ran_at: str
    success: bool
    output: str
    returncode: int

    @staticmethod
    def from_result(job_name: str, result) -> "HistoryEntry":
        return HistoryEntry(
            job_name=job_name,
            ran_at=datetime.utcnow().isoformat(),
            success=result.success,
            output=result.output,
            returncode=result.returncode,
        )


class JobHistory:
    """Persists job run history to a JSON lines file."""

    def __init__(self, path: str, max_entries: int = 500) -> None:
        self._path = path
        self._max_entries = max_entries

    def record(self, entry: HistoryEntry) -> None:
        """Append a new history entry, pruning oldest if over limit."""
        entries = self.load()
        entries.append(entry)
        if len(entries) > self._max_entries:
            entries = entries[-self._max_entries :]
        self._write(entries)

    def load(self) -> List[HistoryEntry]:
        """Return all stored history entries."""
        if not os.path.exists(self._path):
            return []
        entries: List[HistoryEntry] = []
        with open(self._path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(HistoryEntry(**data))
        return entries

    def last_for(self, job_name: str) -> Optional[HistoryEntry]:
        """Return the most recent entry for a given job, or None."""
        matches = [e for e in self.load() if e.job_name == job_name]
        return matches[-1] if matches else None

    def _write(self, entries: List[HistoryEntry]) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(asdict(entry)) + "\n")
