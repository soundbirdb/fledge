"""Cron expression parsing and scheduling support for fledge jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class CronPolicy:
    expression: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CronPolicy":
        return cls(expression=data.get("cron") or None)

    @property
    def enabled(self) -> bool:
        return bool(self.expression)


def _parse_field(value: str, min_val: int, max_val: int) -> List[int]:
    """Parse a single cron field into a sorted list of matching integers."""
    if value == "*":
        return list(range(min_val, max_val + 1))

    result: List[int] = []
    for part in value.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = min_val if base == "*" else int(base)
            result.extend(range(start, max_val + 1, int(step)))
        elif "-" in part:
            lo, hi = part.split("-", 1)
            result.extend(range(int(lo), int(hi) + 1))
        else:
            result.append(int(part))

    return sorted(set(v for v in result if min_val <= v <= max_val))


def parse_cron(expression: str):
    """Return a callable that accepts a datetime and returns True if it matches."""
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression (expected 5 fields): {expression!r}")

    minutes = _parse_field(parts[0], 0, 59)
    hours = _parse_field(parts[1], 0, 23)
    days = _parse_field(parts[2], 1, 31)
    months = _parse_field(parts[3], 1, 12)
    weekdays = _parse_field(parts[4], 0, 6)

    def matches(dt: datetime) -> bool:
        return (
            dt.minute in minutes
            and dt.hour in hours
            and dt.day in days
            and dt.month in months
            and dt.weekday() in [w % 7 for w in weekdays]
        )

    return matches
