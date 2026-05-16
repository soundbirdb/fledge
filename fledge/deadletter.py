"""Dead-letter queue: persist jobs that have exhausted all retries."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fledge.runner import JobResult


@dataclass
class DeadLetterEntry:
    job_name: str
    command: str
    failed_at: str
    exit_code: Optional[int]
    stderr: str
    attempts: int

    @classmethod
    def from_result(cls, result: JobResult, attempts: int) -> "DeadLetterEntry":
        return cls(
            job_name=result.job_name,
            command=result.command,
            failed_at=datetime.now(timezone.utc).isoformat(),
            exit_code=result.exit_code,
            stderr=result.stderr or "",
            attempts=attempts,
        )

    def as_dict(self) -> dict:
        return asdict(self)


class DeadLetterQueue:
    def __init__(self, path: str = "dead_letters.jsonl") -> None:
        self._path = Path(path)

    def push(self, entry: DeadLetterEntry) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.as_dict()) + "\n")

    def load_all(self) -> List[DeadLetterEntry]:
        if not self._path.exists():
            return []
        entries: List[DeadLetterEntry] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(DeadLetterEntry(**data))
        return entries

    def clear(self) -> int:
        if not self._path.exists():
            return 0
        entries = self.load_all()
        count = len(entries)
        self._path.unlink()
        return count

    @property
    def size(self) -> int:
        return len(self.load_all())
