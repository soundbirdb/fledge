"""Tests for fledge.priority."""
import pytest

from fledge.priority import (
    PriorityPolicy,
    PriorityQueue,
    _DEFAULT_PRIORITY,
    _MAX_PRIORITY,
    _MIN_PRIORITY,
)


class TestPriorityPolicy:
    def test_defaults(self):
        p = PriorityPolicy()
        assert p.level == _DEFAULT_PRIORITY

    def test_from_dict_full(self):
        p = PriorityPolicy.from_dict({"level": 10})
        assert p.level == 10

    def test_from_dict_empty(self):
        p = PriorityPolicy.from_dict({})
        assert p.level == _DEFAULT_PRIORITY

    def test_from_dict_string_coerced(self):
        p = PriorityPolicy.from_dict({"level": "20"})
        assert p.level == 20

    def test_from_dict_clamps_above_max(self):
        p = PriorityPolicy.from_dict({"level": 999})
        assert p.level == _MAX_PRIORITY

    def test_from_dict_clamps_below_min(self):
        p = PriorityPolicy.from_dict({"level": -5})
        assert p.level == _MIN_PRIORITY

    def test_from_dict_invalid_string_uses_default(self):
        p = PriorityPolicy.from_dict({"level": "high"})
        assert p.level == _DEFAULT_PRIORITY

    def test_enabled_always_true(self):
        assert PriorityPolicy().enabled is True


class TestPriorityQueue:
    @pytest.fixture()
    def queue(self):
        q = PriorityQueue()
        q.register("low_job", PriorityPolicy.from_dict({"level": 80}))
        q.register("high_job", PriorityPolicy.from_dict({"level": 10}))
        q.register("mid_job", PriorityPolicy.from_dict({"level": 50}))
        return q

    def test_sorted_jobs_highest_first(self, queue):
        result = queue.sorted_jobs(["low_job", "high_job", "mid_job"])
        assert result == ["high_job", "mid_job", "low_job"]

    def test_unregistered_job_uses_default(self, queue):
        result = queue.sorted_jobs(["unknown", "high_job"])
        # unknown gets default (50), high_job is 10 → high_job first
        assert result[0] == "high_job"
        assert result[1] == "unknown"

    def test_level_for_registered(self, queue):
        assert queue.level_for("high_job") == 10

    def test_level_for_unregistered_returns_default(self, queue):
        assert queue.level_for("ghost_job") == _DEFAULT_PRIORITY

    def test_empty_list_returns_empty(self, queue):
        assert queue.sorted_jobs([]) == []

    def test_single_job_returned_unchanged(self, queue):
        assert queue.sorted_jobs(["low_job"]) == ["low_job"]
