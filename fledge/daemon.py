"""Daemon: orchestrates scheduler, runner, and all job policies."""
from __future__ import annotations

import time
from typing import Dict

from fledge.config import FledgeConfig
from fledge.scheduler import Scheduler
from fledge.runner import JobRunner
from fledge.metrics import MetricsCollector
from fledge.circuit_breaker import CircuitBreakerPolicy, CircuitBreaker, BreakerState
from fledge.quota import QuotaPolicy, QuotaTracker
from fledge.tagging import TagPolicy
from fledge.runonce import RunOncePolicy, RunOnceTracker
from fledge.pausing import PausePolicy, PauseRegistry
from fledge.eventbus import EventBus, JobEvent
from fledge.budget import BudgetPolicy, BudgetTracker


class Daemon:
    def __init__(self, config: FledgeConfig) -> None:
        self._config = config
        self._scheduler = Scheduler(config.jobs)
        self._runner = JobRunner()
        self._metrics = MetricsCollector()
        self._running = False
        self.event_bus = EventBus()

        # Per-job policy registries
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._quota_trackers: Dict[str, QuotaTracker] = {}
        self._tag_registry: Dict[str, TagPolicy] = {}
        self._runonce_trackers: Dict[str, RunOnceTracker] = {}
        self._budget_trackers: Dict[str, BudgetTracker] = {}

        for job in config.jobs:
            extra = job.extra

            cb_policy = CircuitBreakerPolicy.from_dict(extra)
            self._breakers[job.name] = CircuitBreaker(cb_policy)

            quota_policy = QuotaPolicy.from_dict(extra)
            self._quota_trackers[job.name] = QuotaTracker(quota_policy)

            self._tag_registry[job.name] = TagPolicy.from_dict(extra)

            ro_policy = RunOncePolicy.from_dict(extra)
            self._runonce_trackers[job.name] = RunOnceTracker(ro_policy)

            budget_policy = BudgetPolicy.from_dict(extra)
            self._budget_trackers[job.name] = BudgetTracker(budget_policy)

        self._pause_registry = PauseRegistry(config)

    @property
    def metrics(self) -> MetricsCollector:
        return self._metrics

    def start(self) -> None:
        self._running = True
        while self._running:
            self._run_due_jobs()
            time.sleep(self._config.daemon.interval)

    def stop(self) -> None:
        self._running = False

    def _run_due_jobs(self) -> None:
        for schedule in self._scheduler.due():
            job = schedule.job
            name = job.name

            if self._pause_registry.is_paused(name):
                continue

            breaker = self._breakers.get(name)
            if breaker and breaker.state == BreakerState.OPEN:
                continue

            quota = self._quota_trackers.get(name)
            if quota and not quota.allowed():
                continue

            runonce = self._runonce_trackers.get(name)
            if runonce and not runonce.allowed(name):
                continue

            budget = self._budget_trackers.get(name)
            if budget and not budget.allowed():
                continue

            self.event_bus.publish(JobEvent.started(name))
            result = self._runner.run(job)
            schedule.mark_ran()

            self._metrics.record(name, result)

            if budget:
                budget.record()
            if quota:
                quota.record()
            if runonce:
                runonce.record(name)
            if breaker:
                if result.success:
                    breaker.record_success()
                else:
                    breaker.record_failure()

            if result.success:
                self.event_bus.publish(JobEvent.succeeded(name))
            else:
                self.event_bus.publish(JobEvent.failed(name, error=str(result.error)))
