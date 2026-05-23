"""Integration tests: budget policy parsed from a full TOML config."""
import textwrap
import pytest
from fledge.config import load_config
from fledge.budget import BudgetPolicy


@pytest.fixture
def config_with_budget(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [jobs.ingest]
        command = "python ingest.py"
        every = 60

        [jobs.ingest.budget]
        max_runs = 100
        window_seconds = 3600
    """))
    return load_config(str(cfg))


@pytest.fixture
def config_no_budget(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""
        [daemon]
        interval = 10

        [jobs.ingest]
        command = "python ingest.py"
        every = 60
    """))
    return load_config(str(cfg))


def test_budget_policy_parsed(config_with_budget):
    job = config_with_budget.jobs[0]
    policy = BudgetPolicy.from_dict(job.extra)
    assert policy.max_runs == 100
    assert policy.window_seconds == 3600
    assert policy.enabled


def test_budget_defaults_when_section_absent(config_no_budget):
    job = config_no_budget.jobs[0]
    policy = BudgetPolicy.from_dict(job.extra)
    assert not policy.enabled
    assert policy.max_runs == 0


def test_budget_from_dict_partial(config_with_budget):
    policy = BudgetPolicy.from_dict({"budget": {"max_runs": 50}})
    assert policy.max_runs == 50
    assert policy.window_seconds == 3600  # default
