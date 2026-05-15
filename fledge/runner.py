import subprocess
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fledge.config import JobConfig

logger = logging.getLogger(__name__)


@dataclass
class JobResult:
    job_name: str
    command: str
    started_at: datetime
    finished_at: datetime
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def success(self) -> bool:
        return self.returncode == 0


class JobRunner:
    """Executes job commands as subprocesses and returns structured results."""

    def __init__(self, timeout: int = 300) -> None:
        self.timeout = timeout

    def run(self, job: JobConfig) -> JobResult:
        started_at = datetime.utcnow()
        logger.info("Running job %r: %s", job.name, job.command)

        try:
            proc = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            returncode = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired:
            logger.error("Job %r timed out after %s seconds", job.name, self.timeout)
            returncode = -1
            stdout = ""
            stderr = f"Timed out after {self.timeout} seconds"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Job %r raised an unexpected error", job.name)
            returncode = -1
            stdout = ""
            stderr = str(exc)

        finished_at = datetime.utcnow()
        result = JobResult(
            job_name=job.name,
            command=job.command,
            started_at=started_at,
            finished_at=finished_at,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

        if result.success:
            logger.info("Job %r finished successfully", job.name)
        else:
            logger.warning("Job %r failed with code %d", job.name, returncode)

        return result
