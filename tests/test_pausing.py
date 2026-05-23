"""Tests for fledge.pausing — PausePolicy and PauseRegistry."""

from __future__ import annotations

import json
import os
import pytest

from fledge.pausing import PausePolicy, PauseRegistry


# ---------------------------------------------------------------------------
# PausePolicy
# ---------------------------------------------------------------------------

class TestPausePolicy:
    def test_defaults(self):
        p = PausePolicy()
        assert p.paused is False

    def test_from_dict_full(self):
        p = PausePolicy.from_dict({"paused": True})
        assert p.paused is True

    def test_from_dict_empty(self):
        p = PausePolicy.from_dict({})
        assert p.paused is False

    def test_from_dict_false(self):
        p = PausePolicy.from_dict({"paused": False})
        assert p.paused is False


# ---------------------------------------------------------------------------
# PauseRegistry — in-memory (no file)
# ---------------------------------------------------------------------------

@pytest.fixture
def registry():
    return PauseRegistry()


def test_not_paused_by_default(registry):
    assert registry.is_paused("job_a") is False


def test_pause_marks_job(registry):
    registry.pause("job_a")
    assert registry.is_paused("job_a") is True


def test_resume_unmarks_job(registry):
    registry.pause("job_a")
    registry.resume("job_a")
    assert registry.is_paused("job_a") is False


def test_resume_noop_when_not_paused(registry):
    registry.resume("job_x")
    assert registry.is_paused("job_x") is False


def test_all_paused_returns_set(registry):
    registry.pause("a")
    registry.pause("b")
    assert registry.all_paused() == {"a", "b"}


def test_seed_pauses_when_policy_true(registry):
    policy = PausePolicy(paused=True)
    registry.seed("job_a", policy)
    assert registry.is_paused("job_a") is True


def test_seed_does_not_pause_when_policy_false(registry):
    policy = PausePolicy(paused=False)
    registry.seed("job_a", policy)
    assert registry.is_paused("job_a") is False


def test_seed_does_not_override_runtime_resume(registry):
    """If job was manually resumed at runtime, seed should not re-pause it."""
    registry.pause("job_a")
    registry.resume("job_a")
    policy = PausePolicy(paused=True)
    registry.seed("job_a", policy)  # already tracked — should be no-op
    assert registry.is_paused("job_a") is False


# ---------------------------------------------------------------------------
# PauseRegistry — persistence
# ---------------------------------------------------------------------------

@pytest.fixture
def pause_file(tmp_path):
    return str(tmp_path / "paused.json")


def test_paused_state_persisted(pause_file):
    reg = PauseRegistry(path=pause_file)
    reg.pause("job_a")
    assert os.path.exists(pause_file)
    with open(pause_file) as fh:
        data = json.load(fh)
    assert "job_a" in data["paused"]


def test_paused_state_loaded_on_init(pause_file):
    reg1 = PauseRegistry(path=pause_file)
    reg1.pause("job_a")
    reg2 = PauseRegistry(path=pause_file)
    assert reg2.is_paused("job_a") is True


def test_resumed_state_removed_from_file(pause_file):
    reg = PauseRegistry(path=pause_file)
    reg.pause("job_a")
    reg.resume("job_a")
    with open(pause_file) as fh:
        data = json.load(fh)
    assert "job_a" not in data["paused"]
