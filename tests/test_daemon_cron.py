"""Tests verifying Daemon respects cron-scheduled jobs."""

import textwrap
import pytest
from unittest.mock import MagicMock, patch

from fledge.config import load_config
from fledge.daemon import Daemon


@pytest.fixture
def cron_config(tmp_path):
    cfg = tmp_path / "fledge.toml"
    cfg.write_text(textwrap.dedent("""\
        [daemon]
        interval = 10

        [[jobs]]
        name = "hourly_cron"
        command = "echo hourly"
        cron = "0 * * * *"

        [[jobs]]
        name = "every_minute"
        command = "echo every"
        cron = "* * * * *"
    """))
    return load_config(cfg)


def _make_daemon(config):
    d = Daemon(config)
    d._runner = MagicMock()
    d._runner.run.return_value = MagicMock(success=True, job_name="every_minute",
                                           duration=0.1, error=None)
    return d


def test_daemon_loads_cron_jobs(cron_config):
    d = _make_daemon(cron_config)
    names = [s.job.name for s in d._scheduler._schedules]
    assert "hourly_cron" in names
    assert "every_minute" in names


def test_cron_job_with_every_minute_is_due(cron_config):
    d = _make_daemon(cron_config)
    due = d._scheduler.due_jobs()
    due_names = [s.job.name for s in due]
    assert "every_minute" in due_names


def test_daemon_run_due_jobs_executes_cron_job(cron_config):
    d = _make_daemon(cron_config)
    # Patch scheduler to only return the every_minute job as due
    every_minute_schedule = next(
        s for s in d._scheduler._schedules if s.job.name == "every_minute"
    )
    with patch.object(d._scheduler, "due_jobs", return_value=[every_minute_schedule]):
        d._run_due_jobs()
    d._runner.run.assert_called_once()
    call_job = d._runner.run.call_args[0][0]
    assert call_job.name == "every_minute"
