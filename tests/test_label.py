"""Tests for fledge.label — LabelPolicy and LabelRegistry."""
import pytest
from fledge.label import LabelPolicy, LabelRegistry


class TestLabelPolicy:
    def test_defaults(self):
        p = LabelPolicy()
        assert p.labels == {}
        assert not p.enabled()

    def test_from_dict_full(self):
        p = LabelPolicy.from_dict({"labels": {"env": "prod", "team": "data"}})
        assert p.labels == {"env": "prod", "team": "data"}
        assert p.enabled()

    def test_from_dict_empty(self):
        p = LabelPolicy.from_dict({})
        assert p.labels == {}
        assert not p.enabled()

    def test_from_dict_csv_string(self):
        p = LabelPolicy.from_dict({"labels": "env=staging, team=ops"})
        assert p.labels == {"env": "staging", "team": "ops"}

    def test_from_dict_csv_string_no_equals_ignored(self):
        p = LabelPolicy.from_dict({"labels": "nodomain, env=prod"})
        assert "env" in p.labels
        assert "nodomain" not in p.labels

    def test_get_existing_key(self):
        p = LabelPolicy(labels={"env": "prod"})
        assert p.get("env") == "prod"

    def test_get_missing_key_returns_default(self):
        p = LabelPolicy(labels={})
        assert p.get("env") is None
        assert p.get("env", "dev") == "dev"

    def test_has_returns_true_for_present_key(self):
        p = LabelPolicy(labels={"region": "eu"})
        assert p.has("region")
        assert not p.has("zone")

    def test_matches_exact_value(self):
        p = LabelPolicy(labels={"env": "prod"})
        assert p.matches("env", "prod")
        assert not p.matches("env", "staging")


class TestLabelRegistry:
    def _registry(self) -> LabelRegistry:
        reg = LabelRegistry()
        reg.register("job_a", LabelPolicy(labels={"env": "prod", "team": "data"}))
        reg.register("job_b", LabelPolicy(labels={"env": "staging"}))
        reg.register("job_c", LabelPolicy())
        return reg

    def test_get_registered_policy(self):
        reg = self._registry()
        assert reg.get("job_a").get("env") == "prod"

    def test_get_unregistered_returns_empty_policy(self):
        reg = self._registry()
        p = reg.get("unknown")
        assert not p.enabled()

    def test_jobs_with_label_key_only(self):
        reg = self._registry()
        jobs = reg.jobs_with_label("env")
        assert jobs == ["job_a", "job_b"]

    def test_jobs_with_label_key_and_value(self):
        reg = self._registry()
        jobs = reg.jobs_with_label("env", "prod")
        assert jobs == ["job_a"]

    def test_jobs_with_label_no_match(self):
        reg = self._registry()
        assert reg.jobs_with_label("nonexistent") == []

    def test_all_labels_excludes_empty(self):
        reg = self._registry()
        result = reg.all_labels()
        assert "job_a" in result
        assert "job_b" in result
        assert "job_c" not in result

    def test_all_labels_values(self):
        reg = self._registry()
        assert reg.all_labels()["job_a"] == {"env": "prod", "team": "data"}
