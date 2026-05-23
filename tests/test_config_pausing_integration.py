"""Integration-level tests: pause state persisted across PauseRegistry instances."""

from __future__ import annotations

import pytest

from fledge.pausing import PauseRegistry, PausePolicy


@pytest.fixture
def state_file(tmp_path):
    return str(tmp_path / "pause_state.json")


def test_pause_survives_reload(state_file):
    r1 = PauseRegistry(path=state_file)
    r1.pause("job_x")

    r2 = PauseRegistry(path=state_file)
    assert r2.is_paused("job_x") is True


def test_resume_survives_reload(state_file):
    r1 = PauseRegistry(path=state_file)
    r1.pause("job_x")
    r1.resume("job_x")

    r2 = PauseRegistry(path=state_file)
    assert r2.is_paused("job_x") is False


def test_multiple_jobs_persisted(state_file):
    r1 = PauseRegistry(path=state_file)
    r1.pause("a")
    r1.pause("b")
    r1.pause("c")
    r1.resume("b")

    r2 = PauseRegistry(path=state_file)
    assert r2.is_paused("a") is True
    assert r2.is_paused("b") is False
    assert r2.is_paused("c") is True


def test_corrupt_file_falls_back_to_empty(state_file):
    with open(state_file, "w") as fh:
        fh.write("not valid json{{")

    r = PauseRegistry(path=state_file)
    assert r.all_paused() == set()


def test_seed_idempotent_across_reloads(state_file):
    """Seeding the same paused job twice should not duplicate entries."""
    r1 = PauseRegistry(path=state_file)
    policy = PausePolicy(paused=True)
    r1.seed("job_a", policy)
    r1.seed("job_a", policy)

    r2 = PauseRegistry(path=state_file)
    assert r2.is_paused("job_a") is True
    # Ensure the stored list has no duplicates
    import json
    with open(state_file) as fh:
        data = json.load(fh)
    assert data["paused"].count("job_a") == 1
