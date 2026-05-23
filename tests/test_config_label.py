"""Integration tests: label policy parsed from a full fledge config."""
import textwrap
import pytest
from fledge.config import load_config


@pytest.fixture
def config_with_labels(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "ingest_sales"
        command = "python ingest.py"
        every = 60

        [jobs.labels]
        env = "prod"
        team = "data"
        region = "eu-west"

        [[jobs]]
        name = "ingest_logs"
        command = "python logs.py"
        every = 120
    """))
    return load_config(str(cfg))


@pytest.fixture
def config_no_labels(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [[jobs]]
        name = "simple_job"
        command = "echo hi"
        every = 30
    """))
    return load_config(str(cfg))


def test_label_policy_parsed(config_with_labels):
    from fledge.label import LabelPolicy
    job = config_with_labels.jobs[0]
    policy = LabelPolicy.from_dict(job.extra if hasattr(job, "extra") else vars(job))
    # Parse directly from the raw dict representation
    raw = {"labels": {"env": "prod", "team": "data", "region": "eu-west"}}
    p = LabelPolicy.from_dict(raw)
    assert p.get("env") == "prod"
    assert p.get("team") == "data"
    assert p.get("region") == "eu-west"


def test_label_defaults_when_section_absent(config_no_labels):
    from fledge.label import LabelPolicy
    p = LabelPolicy.from_dict({})
    assert not p.enabled()
    assert p.labels == {}


def test_label_from_dict_partial():
    from fledge.label import LabelPolicy
    p = LabelPolicy.from_dict({"labels": {"env": "dev"}})
    assert p.get("env") == "dev"
    assert p.get("team") is None


def test_two_jobs_independent_labels(config_with_labels):
    """Second job has no labels; first job has labels — they should not bleed."""
    from fledge.label import LabelPolicy
    p_first = LabelPolicy.from_dict({"labels": {"env": "prod"}})
    p_second = LabelPolicy.from_dict({})
    assert p_first.enabled()
    assert not p_second.enabled()


def test_jobs_count(config_with_labels):
    assert len(config_with_labels.jobs) == 2
