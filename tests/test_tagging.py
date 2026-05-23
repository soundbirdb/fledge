"""Tests for fledge.tagging."""
import pytest
from fledge.tagging import TagPolicy, TagRegistry


class TestTagPolicy:
    def test_defaults(self):
        p = TagPolicy()
        assert p.tags == []
        assert not p.enabled

    def test_from_dict_list(self):
        p = TagPolicy.from_dict({"tags": ["etl", "nightly"]})
        assert p.tags == ["etl", "nightly"]
        assert p.enabled

    def test_from_dict_csv_string(self):
        p = TagPolicy.from_dict({"tags": "etl, nightly, critical"})
        assert p.tags == ["etl", "nightly", "critical"]

    def test_from_dict_empty(self):
        p = TagPolicy.from_dict({})
        assert p.tags == []
        assert not p.enabled

    def test_from_dict_strips_whitespace(self):
        p = TagPolicy.from_dict({"tags": ["  etl ", " nightly"]})
        assert p.tags == ["etl", "nightly"]

    def test_has_tag_true(self):
        p = TagPolicy(tags=["etl", "nightly"])
        assert p.has_tag("etl")

    def test_has_tag_false(self):
        p = TagPolicy(tags=["etl"])
        assert not p.has_tag("critical")

    def test_matches_any(self):
        p = TagPolicy(tags=["etl", "nightly"])
        assert p.matches_any(["nightly", "critical"])
        assert not p.matches_any(["critical", "fast"])

    def test_matches_all(self):
        p = TagPolicy(tags=["etl", "nightly", "critical"])
        assert p.matches_all(["etl", "nightly"])
        assert not p.matches_all(["etl", "missing"])

    def test_tag_set(self):
        p = TagPolicy(tags=["a", "b", "a"])
        assert p.tag_set == {"a", "b"}


class TestTagRegistry:
    @pytest.fixture()
    def registry(self):
        r = TagRegistry()
        r.register("job_a", TagPolicy(tags=["etl", "nightly"]))
        r.register("job_b", TagPolicy(tags=["etl", "critical"]))
        r.register("job_c", TagPolicy(tags=["reporting"]))
        return r

    def test_tags_for_known_job(self, registry):
        assert registry.tags_for("job_a") == ["etl", "nightly"]

    def test_tags_for_unknown_job(self, registry):
        assert registry.tags_for("ghost") == []

    def test_jobs_with_tag(self, registry):
        result = registry.jobs_with_tag("etl")
        assert set(result) == {"job_a", "job_b"}

    def test_jobs_with_tag_none(self, registry):
        assert registry.jobs_with_tag("unknown") == []

    def test_jobs_matching_any(self, registry):
        result = registry.jobs_matching_any(["nightly", "reporting"])
        assert set(result) == {"job_a", "job_c"}

    def test_jobs_matching_all(self, registry):
        result = registry.jobs_matching_all(["etl", "critical"])
        assert result == ["job_b"]

    def test_all_tags(self, registry):
        assert registry.all_tags() == {"etl", "nightly", "critical", "reporting"}

    def test_register_overwrites_existing_job(self, registry):
        """Re-registering a job should replace its tag policy."""
        registry.register("job_a", TagPolicy(tags=["batch"]))
        assert registry.tags_for("job_a") == ["batch"]
        # job_a should no longer appear under its old tags
        assert "job_a" not in registry.jobs_with_tag("etl")
        assert "job_a" not in registry.jobs_with_tag("nightly")
