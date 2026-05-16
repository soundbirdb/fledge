"""Tests for fledge.window — execution window policy."""
from datetime import datetime, time

import pytest

from fledge.window import WindowPolicy, _parse_time


class TestWindowPolicy:
    def test_defaults(self):
        p = WindowPolicy()
        assert p.windows == []
        assert not p.enabled()

    def test_from_dict_empty(self):
        p = WindowPolicy.from_dict({})
        assert not p.enabled()

    def test_from_dict_single_window(self):
        p = WindowPolicy.from_dict({"window": ["09:00-17:00"]})
        assert p.enabled()
        assert len(p.windows) == 1
        assert p.windows[0] == (time(9, 0), time(17, 0))

    def test_from_dict_csv_string(self):
        p = WindowPolicy.from_dict({"window": "08:00-12:00, 13:00-18:00"})
        assert len(p.windows) == 2

    def test_from_dict_multiple_list(self):
        p = WindowPolicy.from_dict({"window": ["08:00-12:00", "13:00-18:00"]})
        assert len(p.windows) == 2

    def test_allows_when_no_windows(self):
        p = WindowPolicy()
        assert p.allows() is True

    def test_allows_within_window(self):
        p = WindowPolicy.from_dict({"window": ["08:00-18:00"]})
        inside = datetime(2024, 1, 1, 12, 0)
        assert p.allows(inside) is True

    def test_denies_outside_window(self):
        p = WindowPolicy.from_dict({"window": ["08:00-18:00"]})
        outside = datetime(2024, 1, 1, 20, 0)
        assert p.allows(outside) is False

    def test_allows_overnight_window_before_midnight(self):
        p = WindowPolicy.from_dict({"window": ["22:00-06:00"]})
        assert p.allows(datetime(2024, 1, 1, 23, 0)) is True

    def test_allows_overnight_window_after_midnight(self):
        p = WindowPolicy.from_dict({"window": ["22:00-06:00"]})
        assert p.allows(datetime(2024, 1, 1, 3, 0)) is True

    def test_denies_outside_overnight_window(self):
        p = WindowPolicy.from_dict({"window": ["22:00-06:00"]})
        assert p.allows(datetime(2024, 1, 1, 12, 0)) is False

    def test_allows_boundary_start(self):
        p = WindowPolicy.from_dict({"window": ["09:00-17:00"]})
        assert p.allows(datetime(2024, 1, 1, 9, 0)) is True

    def test_allows_boundary_end(self):
        p = WindowPolicy.from_dict({"window": ["09:00-17:00"]})
        assert p.allows(datetime(2024, 1, 1, 17, 0)) is True

    def test_invalid_window_entry_skipped(self):
        p = WindowPolicy.from_dict({"window": ["not-a-time"]})
        assert p.windows == []


class TestParseTime:
    def test_hhmm(self):
        assert _parse_time("09:30") == time(9, 30)

    def test_hhmmss(self):
        assert _parse_time("09:30:00") == time(9, 30, 0)

    def test_invalid_returns_none(self):
        assert _parse_time("nope") is None
