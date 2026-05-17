"""Tests for RunOncePolicy and RunOnceTracker."""
from __future__ import annotations

import json
import os
import pytest

from fledge.runonce import RunOncePolicy, RunOnceTracker


# ---------------------------------------------------------------------------
# RunOncePolicy
# ---------------------------------------------------------------------------

class TestRunOncePolicy:
    def test_defaults(self):
        p = RunOncePolicy()
        assert p.enabled is False
        assert p.scope == "day"

    def test_from_dict_full(self):
        p = RunOncePolicy.from_dict({"run_once": {"enabled": True, "scope": "forever"}})
        assert p.enabled is True
        assert p.scope == "forever"

    def test_from_dict_empty(self):
        p = RunOncePolicy.from_dict({})
        assert p.enabled is False

    def test_from_dict_partial(self):
        p = RunOncePolicy.from_dict({"run_once": {"enabled": True}})
        assert p.enabled is True
        assert p.scope == "day"

    def test_from_dict_missing_key(self):
        p = RunOncePolicy.from_dict({"run_once": {}})
        assert p.enabled is False
        assert p.scope == "day"


# ---------------------------------------------------------------------------
# RunOnceTracker
# ---------------------------------------------------------------------------

@pytest.fixture
def tracker_file(tmp_path):
    return str(tmp_path / "runonce.json")


@pytest.fixture
def tracker(tracker_file):
    return RunOnceTracker(path=tracker_file)


def test_has_run_false_initially(tracker):
    assert tracker.has_run("job_a", "day") is False


def test_record_marks_job(tracker):
    tracker.record("job_a")
    assert tracker.has_run("job_a", "day") is True


def test_has_run_forever_after_record(tracker):
    tracker.record("job_a")
    assert tracker.has_run("job_a", "forever") is True


def test_has_run_forever_without_record(tracker):
    assert tracker.has_run("job_a", "forever") is False


def test_reset_specific_job(tracker):
    tracker.record("job_a")
    tracker.record("job_b")
    tracker.reset("job_a")
    assert tracker.has_run("job_a", "day") is False
    assert tracker.has_run("job_b", "day") is True


def test_reset_all(tracker):
    tracker.record("job_a")
    tracker.record("job_b")
    tracker.reset()
    assert tracker.has_run("job_a", "day") is False
    assert tracker.has_run("job_b", "day") is False


def test_persists_to_disk(tracker_file):
    t1 = RunOnceTracker(path=tracker_file)
    t1.record("job_x")
    t2 = RunOnceTracker(path=tracker_file)
    assert t2.has_run("job_x", "day") is True


def test_corrupt_file_handled_gracefully(tracker_file):
    with open(tracker_file, "w") as fh:
        fh.write("not-json")
    t = RunOnceTracker(path=tracker_file)
    assert t.has_run("job_a", "day") is False
