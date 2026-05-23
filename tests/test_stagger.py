"""Tests for fledge.stagger."""
from __future__ import annotations

import time
import pytest

from fledge.stagger import StaggerPolicy, StaggerTracker


class TestStaggerPolicy:
    def test_defaults(self):
        p = StaggerPolicy()
        assert p.enabled is False
        assert p.spread_seconds == 0.0

    def test_from_dict_full(self):
        p = StaggerPolicy.from_dict({"stagger": {"spread_seconds": 10.0}})
        assert p.enabled is True
        assert p.spread_seconds == 10.0

    def test_from_dict_empty(self):
        p = StaggerPolicy.from_dict({})
        assert p.enabled is False

    def test_from_dict_zero_disables(self):
        p = StaggerPolicy.from_dict({"stagger": {"spread_seconds": 0}})
        assert p.enabled is False

    def test_from_dict_negative_clamped(self):
        p = StaggerPolicy.from_dict({"stagger": {"spread_seconds": -5}})
        assert p.spread_seconds == 0.0
        assert p.enabled is False

    def test_from_dict_string_coerced(self):
        p = StaggerPolicy.from_dict({"stagger": {"spread_seconds": "8"}})
        assert p.spread_seconds == 8.0
        assert p.enabled is True


class TestStaggerTracker:
    def _policy(self, spread: float = 10.0) -> StaggerPolicy:
        return StaggerPolicy(enabled=spread > 0, spread_seconds=spread)

    def test_offset_zero_when_disabled(self):
        tracker = StaggerTracker(StaggerPolicy())
        tracker.register("job_a")
        assert tracker.offset_for("job_a") == 0.0

    def test_offsets_distributed_evenly(self):
        tracker = StaggerTracker(self._policy(10.0))
        tracker.register("job_a")
        tracker.register("job_b")
        tracker.register("job_c")
        offsets = [tracker.offset_for(n) for n in ("job_a", "job_b", "job_c")]
        # offsets should be non-decreasing and distinct
        assert offsets[0] < offsets[1] < offsets[2]

    def test_first_job_offset_is_zero(self):
        tracker = StaggerTracker(self._policy(30.0))
        tracker.register("first")
        assert tracker.offset_for("first") == 0.0

    def test_is_clear_immediately_for_disabled(self):
        tracker = StaggerTracker(StaggerPolicy())
        tracker.register("job")
        assert tracker.is_clear("job") is True

    def test_is_clear_false_before_offset_elapses(self):
        tracker = StaggerTracker(self._policy(spread=60.0))
        tracker.register("job_a")
        tracker.register("job_b")  # second job gets offset > 0
        # job_b offset = 30s; we haven't waited 30s
        assert tracker.is_clear("job_b") is False

    def test_is_clear_true_for_first_job_immediately(self):
        tracker = StaggerTracker(self._policy(60.0))
        tracker.register("only")
        assert tracker.is_clear("only") is True

    def test_register_idempotent(self):
        tracker = StaggerTracker(self._policy(10.0))
        tracker.register("job")
        tracker.register("job")
        assert tracker._count == 1

    def test_unknown_job_returns_zero_offset(self):
        tracker = StaggerTracker(self._policy(10.0))
        assert tracker.offset_for("ghost") == 0.0
