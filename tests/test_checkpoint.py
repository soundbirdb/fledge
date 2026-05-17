"""Tests for fledge.checkpoint."""

from __future__ import annotations

import json
import pytest

from fledge.checkpoint import CheckpointPolicy, CheckpointStore


# ---------------------------------------------------------------------------
# CheckpointPolicy
# ---------------------------------------------------------------------------

class TestCheckpointPolicy:
    def test_defaults(self):
        p = CheckpointPolicy()
        assert p.enabled is False
        assert p.path == "fledge_checkpoints.json"

    def test_from_dict_full(self):
        p = CheckpointPolicy.from_dict(
            {"checkpoint": {"enabled": True, "path": "/tmp/cp.json"}}
        )
        assert p.enabled is True
        assert p.path == "/tmp/cp.json"

    def test_from_dict_empty(self):
        p = CheckpointPolicy.from_dict({})
        assert p.enabled is False
        assert p.path == "fledge_checkpoints.json"

    def test_from_dict_partial(self):
        p = CheckpointPolicy.from_dict({"checkpoint": {"enabled": True}})
        assert p.enabled is True
        assert p.path == "fledge_checkpoints.json"

    def test_from_dict_no_checkpoint_key(self):
        p = CheckpointPolicy.from_dict({"other": "stuff"})
        assert p.enabled is False


# ---------------------------------------------------------------------------
# CheckpointStore
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    return CheckpointStore(str(tmp_path / "checkpoints.json"))


def test_get_returns_none_for_unknown_job(store):
    assert store.get("job_a") is None


def test_set_and_get_roundtrip(store):
    store.set("job_a", "2024-01-01T00:00:00")
    assert store.get("job_a") == "2024-01-01T00:00:00"


def test_set_persists_to_disk(tmp_path):
    path = str(tmp_path / "cp.json")
    s1 = CheckpointStore(path)
    s1.set("job_b", 42)

    s2 = CheckpointStore(path)
    assert s2.get("job_b") == 42


def test_set_overwrites_existing(store):
    store.set("job_a", "v1")
    store.set("job_a", "v2")
    assert store.get("job_a") == "v2"


def test_clear_removes_entry(store):
    store.set("job_a", "cursor")
    store.clear("job_a")
    assert store.get("job_a") is None


def test_clear_nonexistent_is_noop(store):
    store.clear("ghost")  # should not raise


def test_all_returns_copy(store):
    store.set("j1", 1)
    store.set("j2", 2)
    snapshot = store.all()
    assert snapshot == {"j1": 1, "j2": 2}
    snapshot["j1"] = 99
    assert store.get("j1") == 1  # original unaffected


def test_corrupt_file_is_silently_reset(tmp_path):
    path = tmp_path / "cp.json"
    path.write_text("not-json", encoding="utf-8")
    s = CheckpointStore(str(path))
    assert s.all() == {}
