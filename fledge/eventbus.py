"""Simple in-process event bus for broadcasting job lifecycle events."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class JobEvent:
    """Represents a job lifecycle event."""

    event_type: str          # e.g. "job.started", "job.succeeded", "job.failed"
    job_name: str
    duration: Optional[float] = None
    error: Optional[str] = None
    extra: Dict = field(default_factory=dict)

    @classmethod
    def started(cls, job_name: str) -> "JobEvent":
        return cls(event_type="job.started", job_name=job_name)

    @classmethod
    def succeeded(cls, job_name: str, duration: float) -> "JobEvent":
        return cls(event_type="job.succeeded", job_name=job_name, duration=duration)

    @classmethod
    def failed(cls, job_name: str, duration: float, error: str) -> "JobEvent":
        return cls(event_type="job.failed", job_name=job_name, duration=duration, error=error)


Handler = Callable[[JobEvent], None]


class EventBus:
    """Publish/subscribe event bus.

    Handlers are registered per event type (or "*" for all events).
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        """Register *handler* to be called when *event_type* is published."""
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        """Remove a previously registered handler (no-op if not present)."""
        try:
            self._handlers[event_type].remove(handler)
        except ValueError:
            pass

    def publish(self, event: JobEvent) -> None:
        """Dispatch *event* to all matching and wildcard handlers."""
        for handler in list(self._handlers.get(event.event_type, [])):
            handler(event)
        for handler in list(self._handlers.get("*", [])):
            handler(event)

    def clear(self) -> None:
        """Remove all registered handlers."""
        self._handlers.clear()
