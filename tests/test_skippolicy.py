"""Tests for fledge.skippolicy."""
from __future__ import annotations

import pytest

from fledge.skippolicy import SkipPolicy, SkipEvaluator


class TestSkipPolicy:
    def test_defaults(self):
        p = SkipPolicy()
        assert p.env_var == ""
        assert p.env_value == ""
        assert p.always is False
        assert p.enabled is False

    def test_from_dict_full(self):
        p = SkipPolicy.from_dict({"skip": {"env_var": "SKIP_JOB", "env_value": "yes", "always": False}})
        assert p.env_var == "SKIP_JOB"
        assert p.env_value == "yes"
        assert p.always is False
        assert p.enabled is True

    def test_from_dict_empty(self):
        p = SkipPolicy.from_dict({})
        assert p.env_var == ""
        assert p.enabled is False

    def test_from_dict_always(self):
        p = SkipPolicy.from_dict({"skip": {"always": True}})
        assert p.always is True
        assert p.enabled is True

    def test_from_dict_non_dict_skip_key(self):
        p = SkipPolicy.from_dict({"skip": "yes"})
        assert p == SkipPolicy()


class TestSkipEvaluator:
    def test_always_skip(self):
        policy = SkipPolicy(always=True)
        ev = SkipEvaluator(policy)
        assert ev.should_skip() is True

    def test_no_skip_by_default(self):
        policy = SkipPolicy()
        ev = SkipEvaluator(policy)
        assert ev.should_skip() is False

    def test_env_var_truthy(self, monkeypatch):
        monkeypatch.setenv("SKIP_ME", "1")
        policy = SkipPolicy(env_var="SKIP_ME")
        ev = SkipEvaluator(policy)
        assert ev.should_skip() is True

    def test_env_var_falsy(self, monkeypatch):
        monkeypatch.setenv("SKIP_ME", "0")
        policy = SkipPolicy(env_var="SKIP_ME")
        ev = SkipEvaluator(policy)
        assert ev.should_skip() is False

    def test_env_var_absent(self, monkeypatch):
        monkeypatch.delenv("SKIP_ME", raising=False)
        policy = SkipPolicy(env_var="SKIP_ME")
        ev = SkipEvaluator(policy)
        assert ev.should_skip() is False

    def test_env_var_with_value_match(self, monkeypatch):
        monkeypatch.setenv("ENV", "staging")
        policy = SkipPolicy(env_var="ENV", env_value="staging")
        ev = SkipEvaluator(policy)
        assert ev.should_skip() is True

    def test_env_var_with_value_no_match(self, monkeypatch):
        monkeypatch.setenv("ENV", "production")
        policy = SkipPolicy(env_var="ENV", env_value="staging")
        ev = SkipEvaluator(policy)
        assert ev.should_skip() is False

    def test_predicate_overrides(self):
        policy = SkipPolicy()
        ev = SkipEvaluator(policy, predicate=lambda: True)
        assert ev.should_skip() is True

    def test_predicate_false_does_not_skip(self):
        policy = SkipPolicy()
        ev = SkipEvaluator(policy, predicate=lambda: False)
        assert ev.should_skip() is False

    def test_always_takes_precedence_over_predicate(self):
        policy = SkipPolicy(always=True)
        ev = SkipEvaluator(policy, predicate=lambda: False)
        assert ev.should_skip() is True
