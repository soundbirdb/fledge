"""Execution window policy — restrict jobs to allowed time ranges."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional, Tuple


@dataclass
class WindowPolicy:
    """Defines one or more allowed time windows (HH:MM-HH:MM) for a job."""

    windows: List[Tuple[time, time]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "WindowPolicy":
        raw = data.get("window", [])
        if isinstance(raw, str):
            raw = [r.strip() for r in raw.split(",") if r.strip()]
        parsed: List[Tuple[time, time]] = []
        for entry in raw:
            start_s, _, end_s = entry.partition("-")
            start = _parse_time(start_s.strip())
            end = _parse_time(end_s.strip())
            if start is not None and end is not None:
                parsed.append((start, end))
        return cls(windows=parsed)

    def enabled(self) -> bool:
        return bool(self.windows)

    def allows(self, at: Optional[datetime] = None) -> bool:
        """Return True if *at* (default: now) falls within any configured window."""
        if not self.enabled():
            return True
        now = (at or datetime.now()).time().replace(second=0, microsecond=0)
        for start, end in self.windows:
            if start <= end:
                if start <= now <= end:
                    return True
            else:  # overnight window e.g. 22:00-06:00
                if now >= start or now <= end:
                    return True
        return False


def _parse_time(value: str) -> Optional[time]:
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None
