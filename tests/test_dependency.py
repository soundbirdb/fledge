"""Tests for fledge.dependency — DependencyPolicy and DependencyTracker."""

import pytest
from fledge.dependency import DependencyPolicy, DependencyTracker


# ---------------------------------------------------------------------------
# DependencyPolicy
# ---------------------------------------------------------------------------

class TestDependencyPolicy:
    def test_defaults(self):
        p = DependencyPolicy()
        assert p.requires == []
        assert p.enabled is False

    def test_from_dict_list(self):
        p = DependencyPolicy.from_dict({"requires": ["ingest", "validate"]})
        assert p.requires == ["ingest", "validate"]
        assert p.enabled is True

    def test_from_dict_csv_string(self):
        p = DependencyPolicy.from_dict({"requires": "ingest, validate"})
        assert p.requires == ["ingest", "validate"]

    def test_from_dict_empty(self):
        p = DependencyPolicy.from_dict({})
        assert p.requires == []
        assert p.enabled is False

    def test_from_dict_single_item(self):
        p = DependencyPolicy.from_dict({"requires": ["fetch"]})
        assert p.requires == ["fetch"]
        assert p.enabled is True


# ---------------------------------------------------------------------------
# DependencyTracker
# ---------------------------------------------------------------------------

@pytest.fixture()
def tracker() -> DependencyTracker:
    return DependencyTracker()


class TestDependencyTracker:
    def test_no_dependencies_always_met(self, tracker):
        policy = DependencyPolicy()
        assert tracker.dependencies_met(policy) is True

    def test_unmet_dependency(self, tracker):
        policy = DependencyPolicy(requires=["ingest"])
        assert tracker.dependencies_met(policy) is False

    def test_met_after_record_success(self, tracker):
        policy = DependencyPolicy(requires=["ingest"])
        tracker.record_success("ingest")
        assert tracker.dependencies_met(policy) is True

    def test_partial_dependencies_not_met(self, tracker):
        policy = DependencyPolicy(requires=["a", "b"])
        tracker.record_success("a")
        assert tracker.dependencies_met(policy) is False

    def test_all_dependencies_met(self, tracker):
        policy = DependencyPolicy(requires=["a", "b"])
        tracker.record_success("a")
        tracker.record_success("b")
        assert tracker.dependencies_met(policy) is True

    def test_blocked_by_returns_unmet(self, tracker):
        policy = DependencyPolicy(requires=["a", "b"])
        tracker.record_success("a")
        assert tracker.blocked_by(policy) == ["b"]

    def test_blocked_by_empty_when_all_met(self, tracker):
        policy = DependencyPolicy(requires=["a"])
        tracker.record_success("a")
        assert tracker.blocked_by(policy) == []

    def test_record_failure_does_not_satisfy_dependency(self, tracker):
        policy = DependencyPolicy(requires=["ingest"])
        tracker.record_failure("ingest")
        assert tracker.dependencies_met(policy) is False

    def test_reset_clears_state(self, tracker):
        policy = DependencyPolicy(requires=["ingest"])
        tracker.record_success("ingest")
        tracker.reset()
        assert tracker.dependencies_met(policy) is False

    def test_succeeded_and_failed_sets(self, tracker):
        tracker.record_success("a")
        tracker.record_failure("b")
        assert "a" in tracker.succeeded
        assert "b" in tracker.failed
        assert "a" not in tracker.failed
