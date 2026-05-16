"""Tests for fledge.audit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from fledge.audit import AuditEntry, AuditLog


class _FakeResult:
    def __init__(
        self,
        job_name="sync",
        success=True,
        exit_code=0,
        duration=1.23,
        error=None,
    ):
        self.job_name = job_name
        self.success = success
        self.exit_code = exit_code
        self.duration = duration
        self.error = error
        self.started_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.finished_at = datetime(2024, 1, 1, 12, 0, 1, tzinfo=timezone.utc)


@pytest.fixture
def audit_file(tmp_path):
    return str(tmp_path / "audit" / "audit.jsonl")


@pytest.fixture
def audit(audit_file):
    return AuditLog(audit_file)


def test_audit_entry_from_result():
    r = _FakeResult()
    entry = AuditEntry.from_result(r)
    assert entry.job_name == "sync"
    assert entry.success is True
    assert entry.exit_code == 0
    assert entry.duration == 1.23
    assert entry.attempt == 1
    assert entry.error is None


def test_audit_entry_from_result_with_attempt():
    r = _FakeResult(success=False, exit_code=1, error="oops")
    entry = AuditEntry.from_result(r, attempt=3)
    assert entry.attempt == 3
    assert entry.success is False
    assert entry.error == "oops"


def test_audit_entry_as_dict_has_all_keys():
    r = _FakeResult()
    entry = AuditEntry.from_result(r)
    d = entry.as_dict()
    for key in ("job_name", "started_at", "finished_at", "success",
                "exit_code", "duration", "attempt", "error"):
        assert key in d


def test_record_creates_file(audit, audit_file):
    r = _FakeResult()
    audit.record(r)
    assert Path(audit_file).exists()


def test_record_writes_valid_json(audit, audit_file):
    r = _FakeResult()
    audit.record(r)
    line = Path(audit_file).read_text().strip()
    data = json.loads(line)
    assert data["job_name"] == "sync"
    assert data["success"] is True


def test_record_appends_multiple_entries(audit):
    audit.record(_FakeResult(job_name="job_a"))
    audit.record(_FakeResult(job_name="job_b"))
    entries = audit.read_all()
    assert len(entries) == 2
    assert entries[0].job_name == "job_a"
    assert entries[1].job_name == "job_b"


def test_read_all_empty_when_no_file(tmp_path):
    log = AuditLog(str(tmp_path / "nonexistent" / "audit.jsonl"))
    assert log.read_all() == []


def test_record_creates_parent_dirs(tmp_path):
    nested = str(tmp_path / "a" / "b" / "c" / "audit.jsonl")
    log = AuditLog(nested)
    log.record(_FakeResult())
    assert Path(nested).exists()
