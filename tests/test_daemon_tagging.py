"""Tests that the Daemon builds and exposes a TagRegistry."""
import textwrap
import pytest
from unittest.mock import MagicMock, patch
from fledge.config import load_config
from fledge.daemon import Daemon
from fledge.tagging import TagRegistry


@pytest.fixture()
def tagged_config(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(
        textwrap.dedent("""
            [daemon]
            interval = 5

            [[jobs]]
            name = "job_etl"
            command = "echo etl"
            schedule = "@hourly"
            tags = ["etl", "nightly"]

            [[jobs]]
            name = "job_report"
            command = "echo report"
            schedule = "@daily"
            tags = ["reporting"]
        """)
    )
    return load_config(str(cfg))


def _make_daemon(cfg):
    with patch("fledge.daemon.JobRunner"), patch("fledge.daemon.Scheduler"):
        return Daemon(cfg)


def test_daemon_has_tag_registry(tagged_config):
    d = _make_daemon(tagged_config)
    assert hasattr(d, "tag_registry")
    assert isinstance(d.tag_registry, TagRegistry)


def test_tag_registry_populated(tagged_config):
    d = _make_daemon(tagged_config)
    assert "etl" in d.tag_registry.all_tags()
    assert "reporting" in d.tag_registry.all_tags()


def test_jobs_with_tag_via_registry(tagged_config):
    d = _make_daemon(tagged_config)
    etl_jobs = d.tag_registry.jobs_with_tag("etl")
    assert "job_etl" in etl_jobs
    assert "job_report" not in etl_jobs


def test_untagged_job_has_empty_tags(tmp_path):
    cfg_path = tmp_path / "fledge.toml"
    cfg_path.write_text(
        textwrap.dedent("""
            [daemon]
            interval = 5

            [[jobs]]
            name = "bare_job"
            command = "echo hi"
            schedule = "@hourly"
        """)
    )
    config = load_config(str(cfg_path))
    d = _make_daemon(config)
    assert d.tag_registry.tags_for("bare_job") == []
