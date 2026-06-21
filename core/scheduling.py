from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from peering_manager.registry import SYSTEM_JOBS_KEY, registry

from .enums import JobStatus
from .models import ScheduledTask

if TYPE_CHECKING:
    from peering_manager.jobs import JobRunner

__all__ = (
    "reconcile_scheduled_task",
    "reconcile_schedules",
    "reconcile_task",
    "run_now",
)


def _cancel_schedule(cls: type[JobRunner]) -> None:
    # Only enqueued-but-not-started jobs are cancelled; a running job is left to
    # finish (its reschedule then no-ops because the row is disabled).
    for job in cls.get_jobs().filter(
        status__in=(JobStatus.PENDING, JobStatus.SCHEDULED)
    ):
        job.delete()


def reconcile_schedules() -> None:
    """
    Make the enqueued schedule match the `ScheduledTask` table. Seeds a row for
    every catalog task on first sight, then enqueues enabled tasks and cancels
    disabled ones. Called at worker startup.
    """
    catalog = registry[SYSTEM_JOBS_KEY]
    for task_key, meta in catalog.items():
        ScheduledTask.objects.get_or_create(
            task=task_key,
            defaults={
                "enabled": meta["enabled_by_default"],
                "interval": meta["default_interval"],
            },
        )

    for row in ScheduledTask.objects.all():
        meta = catalog.get(row.task)
        if meta is None:
            continue
        if row.enabled:
            meta["cls"].enqueue_once(interval=row.interval)
        else:
            _cancel_schedule(meta["cls"])


def reconcile_task(task_key: str) -> None:
    """
    Reconcile a single task after its `ScheduledTask` row changed (or after a
    run completes). An enabled task is scheduled one interval out rather than
    run immediately, so editing the interval doesn't force an instant run.
    """
    meta = registry[SYSTEM_JOBS_KEY].get(task_key)
    if meta is None:
        return

    cls = meta["cls"]
    row = ScheduledTask.objects.filter(task=task_key).first()
    if row and row.enabled:
        cls.enqueue_once(
            interval=row.interval,
            schedule_at=timezone.now() + timedelta(minutes=row.interval),
        )
    else:
        _cancel_schedule(cls)


def reconcile_scheduled_task(sender, instance, **kwargs) -> None:
    transaction.on_commit(lambda: reconcile_task(instance.task))


def run_now(task_key: str):
    """
    Clear any enqueued or stuck jobs for a task and queue an immediate run.
    Recovers a task left stuck after a worker died mid-run, and doubles as a manual
    trigger.
    """
    meta = registry[SYSTEM_JOBS_KEY].get(task_key)
    if meta is None:
        return None

    cls = meta["cls"]
    for job in cls.get_jobs().filter(status__in=JobStatus.ENQUEUED_STATE_CHOICES):
        job.delete()

    row = ScheduledTask.objects.filter(task=task_key).first()
    interval = row.interval if row else meta["default_interval"]
    return cls.enqueue_once(interval=interval)
