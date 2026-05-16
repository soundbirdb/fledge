"""Tests for fledge.cron — CronPolicy and parse_cron."""

import pytest
from datetime import datetime

from fledge.cron import CronPolicy, parse_cron, _parse_field


class TestCronPolicy:
    def test_defaults(self):
        p = CronPolicy()
        assert p.expression is None
        assert not p.enabled

    def test_from_dict_with_cron(self):
        p = CronPolicy.from_dict({"cron": "*/5 * * * *"})
        assert p.expression == "*/5 * * * *"
        assert p.enabled

    def test_from_dict_empty(self):
        p = CronPolicy.from_dict({})
        assert p.expression is None
        assert not p.enabled

    def test_from_dict_empty_string_disables(self):
        p = CronPolicy.from_dict({"cron": ""})
        assert not p.enabled


class TestParseField:
    def test_wildcard(self):
        assert _parse_field("*", 0, 4) == [0, 1, 2, 3, 4]

    def test_single_value(self):
        assert _parse_field("3", 0, 59) == [3]

    def test_range(self):
        assert _parse_field("1-3", 0, 59) == [1, 2, 3]

    def test_step(self):
        assert _parse_field("*/15", 0, 59) == [0, 15, 30, 45]

    def test_list(self):
        assert _parse_field("1,3,5", 0, 59) == [1, 3, 5]

    def test_out_of_range_excluded(self):
        assert _parse_field("0,60", 0, 59) == [0]


class TestParseCron:
    def _dt(self, minute=0, hour=0, day=1, month=1, weekday=0):
        # weekday: 0=Monday in Python's datetime
        # Find a date matching the given weekday in January 2024
        base = datetime(2024, month, day, hour, minute)
        return base

    def test_every_minute(self):
        matches = parse_cron("* * * * *")
        assert matches(datetime(2024, 6, 15, 12, 30))

    def test_specific_minute_and_hour(self):
        matches = parse_cron("30 9 * * *")
        assert matches(datetime(2024, 6, 15, 9, 30))
        assert not matches(datetime(2024, 6, 15, 9, 31))
        assert not matches(datetime(2024, 6, 15, 10, 30))

    def test_specific_day_of_month(self):
        matches = parse_cron("0 0 15 * *")
        assert matches(datetime(2024, 6, 15, 0, 0))
        assert not matches(datetime(2024, 6, 14, 0, 0))

    def test_specific_month(self):
        matches = parse_cron("0 0 1 6 *")
        assert matches(datetime(2024, 6, 1, 0, 0))
        assert not matches(datetime(2024, 5, 1, 0, 0))

    def test_step_expression(self):
        matches = parse_cron("*/10 * * * *")
        assert matches(datetime(2024, 1, 1, 0, 0))
        assert matches(datetime(2024, 1, 1, 0, 10))
        assert not matches(datetime(2024, 1, 1, 0, 5))

    def test_invalid_expression_raises(self):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            parse_cron("* * * *")  # only 4 fields
