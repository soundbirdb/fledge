"""Tests for fledge.history."""

import os
import pytest

from fledge.history import HistoryEntry, JobHistory


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, success=True, output="ok", returncode=0):
        self.success = success
        self.output = output
        self.returncode = returncode


@pytest.fixture()
def history_file(tmp_path):
    return str(tmp_path / "history.jsonl")


@pytest.fixture()
def history(history_file):
    return JobHistory(history_file)


# ---------------------------------------------------------------------------
# HistoryEntry
# ---------------------------------------------------------------------------

def test_history_entry_from_result():
    result = _FakeResult(success=True, output="done", returncode=0)
    entry = HistoryEntry.from_result("ingest_sales", result)
    assert entry.job_name == "ingest_sales"
    assert entry.success is True
    assert entry.output == "done"
    assert entry.returncode == 0
    assert entry.ran_at  # non-empty ISO timestamp


# ---------------------------------------------------------------------------
# JobHistory.record / load
# ---------------------------------------------------------------------------

def test_load_returns_empty_when_no_file(history):
    assert history.load() == []


def test_record_and_load_roundtrip(history):
    entry = HistoryEntry("job_a", "2024-01-01T00:00:00", True, "output", 0)
    history.record(entry)
    loaded = history.load()
    assert len(loaded) == 1
    assert loaded[0].job_name == "job_a"
    assert loaded[0].success is True


def test_multiple_entries_preserved(history):
    for i in range(3):
        history.record(HistoryEntry(f"job_{i}", "2024-01-01T00:00:00", True, "", 0))
    assert len(history.load()) == 3


def test_max_entries_pruned(history_file):
    hist = JobHistory(history_file, max_entries=5)
    for i in range(8):
        hist.record(HistoryEntry("job", f"2024-01-0{i % 9 + 1}T00:00:00", True, str(i), 0))
    entries = hist.load()
    assert len(entries) == 5
    # Most recent 5 kept — last output should be "7"
    assert entries[-1].output == "7"


# ---------------------------------------------------------------------------
# JobHistory.last_for
# ---------------------------------------------------------------------------

def test_last_for_returns_none_when_no_match(history):
    history.record(HistoryEntry("other_job", "2024-01-01T00:00:00", True, "", 0))
    assert history.last_for("missing_job") is None


def test_last_for_returns_most_recent(history):
    history.record(HistoryEntry("job_x", "2024-01-01T00:00:00", False, "first", 1))
    history.record(HistoryEntry("job_x", "2024-01-02T00:00:00", True, "second", 0))
    last = history.last_for("job_x")
    assert last is not None
    assert last.output == "second"
    assert last.success is True
