"""Tests for fledge.snapshot."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from fledge.snapshot import JobSnapshot, SnapshotStore


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, job_name, success, duration, error=None):
        self.job_name = job_name
        self.success = success
        self.duration = duration
        self.error = error
        self.finished_at = time.time()


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def snap_file(tmp_path) -> Path:
    return tmp_path / "snapshots.json"


@pytest.fixture
def store(snap_file) -> SnapshotStore:
    return SnapshotStore(str(snap_file))


# ---------------------------------------------------------------------------
# JobSnapshot
# ---------------------------------------------------------------------------

def test_snapshot_from_success_result():
    r = _FakeResult("ingest", success=True, duration=1.5)
    snap = JobSnapshot.from_result(r)
    assert snap.job_name == "ingest"
    assert snap.last_status == "success"
    assert snap.last_error is None
    assert snap.last_duration == pytest.approx(1.5)


def test_snapshot_from_failure_result():
    r = _FakeResult("ingest", success=False, duration=0.3, error="timeout")
    snap = JobSnapshot.from_result(r)
    assert snap.last_status == "failure"
    assert snap.last_error == "timeout"


def test_snapshot_as_dict_has_expected_keys():
    r = _FakeResult("job", success=True, duration=2.0)
    d = JobSnapshot.from_result(r).as_dict()
    assert set(d.keys()) == {"job_name", "last_status", "last_run_at", "last_duration", "last_error"}


# ---------------------------------------------------------------------------
# SnapshotStore
# ---------------------------------------------------------------------------

def test_get_returns_none_for_unknown_job(store):
    assert store.get("missing") is None


def test_update_stores_snapshot(store):
    r = _FakeResult("fetch", success=True, duration=0.8)
    store.update(r)
    snap = store.get("fetch")
    assert snap is not None
    assert snap.last_status == "success"


def test_update_overwrites_previous_snapshot(store):
    store.update(_FakeResult("fetch", success=True, duration=1.0))
    store.update(_FakeResult("fetch", success=False, duration=0.1, error="err"))
    assert store.get("fetch").last_status == "failure"


def test_flush_writes_json_file(store, snap_file):
    store.update(_FakeResult("job_a", success=True, duration=0.5))
    assert snap_file.exists()
    data = json.loads(snap_file.read_text())
    assert "job_a" in data


def test_load_restores_snapshots_from_disk(snap_file):
    s1 = SnapshotStore(str(snap_file))
    s1.update(_FakeResult("persistent", success=True, duration=3.0))

    s2 = SnapshotStore(str(snap_file))
    snap = s2.get("persistent")
    assert snap is not None
    assert snap.last_status == "success"


def test_all_returns_all_snapshots(store):
    store.update(_FakeResult("a", success=True, duration=1.0))
    store.update(_FakeResult("b", success=False, duration=0.2))
    assert set(store.all().keys()) == {"a", "b"}


def test_corrupt_file_is_ignored_gracefully(snap_file):
    snap_file.write_text("{invalid json")
    store = SnapshotStore(str(snap_file))
    assert store.all() == {}
