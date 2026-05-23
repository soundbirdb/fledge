"""Tests for fledge.eventbus."""

import pytest

from fledge.eventbus import EventBus, JobEvent


# ---------------------------------------------------------------------------
# JobEvent construction helpers
# ---------------------------------------------------------------------------

class TestJobEvent:
    def test_started_factory(self):
        ev = JobEvent.started("ingest")
        assert ev.event_type == "job.started"
        assert ev.job_name == "ingest"
        assert ev.duration is None
        assert ev.error is None

    def test_succeeded_factory(self):
        ev = JobEvent.succeeded("ingest", duration=1.23)
        assert ev.event_type == "job.succeeded"
        assert ev.duration == pytest.approx(1.23)

    def test_failed_factory(self):
        ev = JobEvent.failed("ingest", duration=0.5, error="boom")
        assert ev.event_type == "job.failed"
        assert ev.error == "boom"

    def test_extra_defaults_to_empty_dict(self):
        ev = JobEvent.started("x")
        assert ev.extra == {}


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------

@pytest.fixture()
def bus() -> EventBus:
    return EventBus()


class TestEventBus:
    def test_subscribe_and_publish(self, bus):
        received = []
        bus.subscribe("job.started", received.append)
        ev = JobEvent.started("myjob")
        bus.publish(ev)
        assert received == [ev]

    def test_wildcard_receives_all_events(self, bus):
        received = []
        bus.subscribe("*", received.append)
        bus.publish(JobEvent.started("a"))
        bus.publish(JobEvent.succeeded("a", 0.1))
        assert len(received) == 2

    def test_specific_handler_does_not_receive_other_types(self, bus):
        received = []
        bus.subscribe("job.succeeded", received.append)
        bus.publish(JobEvent.started("a"))
        assert received == []

    def test_multiple_handlers_same_event(self, bus):
        calls = []
        bus.subscribe("job.started", lambda e: calls.append(1))
        bus.subscribe("job.started", lambda e: calls.append(2))
        bus.publish(JobEvent.started("x"))
        assert calls == [1, 2]

    def test_unsubscribe_removes_handler(self, bus):
        received = []
        handler = received.append
        bus.subscribe("job.started", handler)
        bus.unsubscribe("job.started", handler)
        bus.publish(JobEvent.started("x"))
        assert received == []

    def test_unsubscribe_nonexistent_is_noop(self, bus):
        bus.unsubscribe("job.started", lambda e: None)  # should not raise

    def test_clear_removes_all_handlers(self, bus):
        received = []
        bus.subscribe("*", received.append)
        bus.subscribe("job.started", received.append)
        bus.clear()
        bus.publish(JobEvent.started("x"))
        assert received == []

    def test_wildcard_and_specific_both_fire(self, bus):
        calls = []
        bus.subscribe("job.failed", lambda e: calls.append("specific"))
        bus.subscribe("*", lambda e: calls.append("wildcard"))
        bus.publish(JobEvent.failed("x", 0.2, "err"))
        assert "specific" in calls
        assert "wildcard" in calls
