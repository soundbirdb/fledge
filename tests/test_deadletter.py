"""Tests for the dead-letter queue."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fledge.deadletter import DeadLetterEntry, DeadLetterQueue


class _FakeResult:
    def __init__(self, job_name="ingest", command="python run.py", exit_code=1, stderr="boom"):
        self.job_name = job_name
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        self.success = False


@pytest.fixture
def dlq_file(tmp_path):
    return str(tmp_path / "dead_letters.jsonl")


@pytest.fixture
def dlq(dlq_file):
    return DeadLetterQueue(path=dlq_file)


def test_entry_from_result():
    result = _FakeResult()
    entry = DeadLetterEntry.from_result(result, attempts=3)
    assert entry.job_name == "ingest"
    assert entry.command == "python run.py"
    assert entry.exit_code == 1
    assert entry.stderr == "boom"
    assert entry.attempts == 3
    assert entry.failed_at  # non-empty ISO timestamp


def test_entry_as_dict_has_expected_keys():
    result = _FakeResult()
    entry = DeadLetterEntry.from_result(result, attempts=2)
    d = entry.as_dict()
    assert set(d.keys()) == {"job_name", "command", "failed_at", "exit_code", "stderr", "attempts"}


def test_push_creates_file(dlq, dlq_file):
    entry = DeadLetterEntry.from_result(_FakeResult(), attempts=1)
    dlq.push(entry)
    assert Path(dlq_file).exists()


def test_push_writes_valid_jsonl(dlq, dlq_file):
    dlq.push(DeadLetterEntry.from_result(_FakeResult(job_name="a"), attempts=1))
    dlq.push(DeadLetterEntry.from_result(_FakeResult(job_name="b"), attempts=2))
    lines = Path(dlq_file).read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["job_name"] == "a"
    assert json.loads(lines[1])["job_name"] == "b"


def test_load_all_returns_entries(dlq):
    dlq.push(DeadLetterEntry.from_result(_FakeResult(job_name="x"), attempts=5))
    entries = dlq.load_all()
    assert len(entries) == 1
    assert entries[0].job_name == "x"
    assert entries[0].attempts == 5


def test_load_all_empty_when_no_file(dlq):
    entries = dlq.load_all()
    assert entries == []


def test_size_reflects_entry_count(dlq):
    assert dlq.size == 0
    dlq.push(DeadLetterEntry.from_result(_FakeResult(), attempts=1))
    dlq.push(DeadLetterEntry.from_result(_FakeResult(), attempts=2))
    assert dlq.size == 2


def test_clear_removes_file_and_returns_count(dlq, dlq_file):
    dlq.push(DeadLetterEntry.from_result(_FakeResult(), attempts=1))
    dlq.push(DeadLetterEntry.from_result(_FakeResult(), attempts=2))
    removed = dlq.clear()
    assert removed == 2
    assert not Path(dlq_file).exists()


def test_clear_on_empty_returns_zero(dlq):
    assert dlq.clear() == 0
