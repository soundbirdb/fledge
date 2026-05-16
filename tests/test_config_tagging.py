"""Integration tests: tagging config parsed from a TOML FledgeConfig."""
import textwrap
import pytest
from fledge.config import load_config
from fledge.tagging import TagPolicy


@pytest.fixture()
def config_with_tags(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""
            [daemon]
            interval = 10

            [[jobs]]
            name = "ingest"
            command = "python ingest.py"
            schedule = "@hourly"
            tags = ["etl", "nightly"]

            [[jobs]]
            name = "report"
            command = "python report.py"
            schedule = "@daily"
            tags = "reporting, critical"
        """)
    )
    return load_config(str(cfg))


@pytest.fixture()
def config_no_tags(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""
            [daemon]
            interval = 10

            [[jobs]]
            name = "ingest"
            command = "python ingest.py"
            schedule = "@hourly"
        """)
    )
    return load_config(str(cfg))


def test_tags_parsed_as_list(config_with_tags):
    job = config_with_tags.jobs[0]
    policy = TagPolicy.from_dict(job.extra.get("tags", {}) if hasattr(job, "extra") else {"tags": job.tags})
    assert "etl" in policy.tags
    assert "nightly" in policy.tags


def test_tags_parsed_from_csv(config_with_tags):
    job = config_with_tags.jobs[1]
    raw = getattr(job, "tags", [])
    policy = TagPolicy.from_dict({"tags": raw})
    assert "reporting" in policy.tags
    assert "critical" in policy.tags


def test_tags_default_empty(config_no_tags):
    job = config_no_tags.jobs[0]
    raw = getattr(job, "tags", [])
    policy = TagPolicy.from_dict({"tags": raw})
    assert policy.tags == []
    assert not policy.enabled
