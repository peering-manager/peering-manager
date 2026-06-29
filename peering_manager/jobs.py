from __future__ import annotations

import contextlib
import logging
import os
import traceback
from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.utils.functional import classproperty
from django_pglocks import advisory_lock
from rq.timeouts import JobTimeoutException

from core.enums import JobStatus, LogLevel
from core.exceptions import JobFailedError
from core.models import Job
from core.scheduling import reconcile_task

from .constants import ADVISORY_LOCK_KEYS
from .registry import SYSTEM_JOBS_KEY, registry

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = (
    "JobRunner",
    "get_scheduled_task",
    "scheduled_task_registry",
    "system_job",
)

# parents[1] is the repo root. Stripped from traceback paths logged on the Job row.
_INSTALL_ROOT = str(Path(__file__).resolve().parents[1]) + os.sep


def system_job(
    interval: int,
    *,
    key: str | None = None,
    label: str | None = None,
    enabled_by_default: bool = True,
    min_interval: int = 1,
) -> Callable[[type[JobRunner]], type[JobRunner]]:
    """
    Register a `JobRunner` as a schedulable task type (the catalog of things
    that can be scheduled).
    """
    if type(interval) is not int:
        raise ImproperlyConfigured("System job interval must be an integer (minutes).")

    def _wrapper(cls: type[JobRunner]) -> type[JobRunner]:
        task_key = key or cls.__name__
        cls.scheduled_task_key = task_key
        registry[SYSTEM_JOBS_KEY][task_key] = {
            "cls": cls,
            "label": label or cls.name,
            "default_interval": interval,
            "enabled_by_default": enabled_by_default,
            "min_interval": min_interval,
        }
        return cls

    return _wrapper


def scheduled_task_registry() -> dict:
    return registry[SYSTEM_JOBS_KEY]


def get_scheduled_task(key: str) -> dict | None:
    return registry[SYSTEM_JOBS_KEY].get(key)


class JobLogHandler(logging.Handler):
    """
    Append `self.logger.*` output to `self.job.data` in memory only. The save happens
    later via `Job.start()` / `Job.terminate()`, collapsing what would otherwise be
    one UPDATE per log line to two per run.
    """

    _LEVEL_MAP = {
        logging.DEBUG: LogLevel.DEFAULT,
        logging.INFO: LogLevel.INFO,
        logging.WARNING: LogLevel.WARNING,
        logging.ERROR: LogLevel.FAILURE,
        logging.CRITICAL: LogLevel.FAILURE,
    }

    def __init__(self, job: Job, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.job = job

    def emit(self, record: logging.LogRecord) -> None:
        if self.job is None or self.job.pk is None:
            return
        level_choice = self._LEVEL_MAP.get(record.levelno, LogLevel.INFO)
        try:
            self.job.log(record.getMessage(), level_choice=level_choice, save=False)
        except Exception:
            self.handleError(record)


class JobRunner(ABC):
    job_timeout: ClassVar[int | None] = None
    scheduled_task_key: ClassVar[str | None] = None

    class Meta:
        name: ClassVar[str | None] = None

    def __init__(self, job: Job) -> None:
        self.job = job
        self.logger = logging.getLogger(f"peering.manager.jobs.{type(self).__name__}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(JobLogHandler(job))

    @classproperty
    def name(cls) -> str:  # noqa: N805
        return getattr(cls.Meta, "name", None) or cls.__name__

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> None:
        """
        Raise `JobFailedError` to terminate with status FAILED. Any other unhandled
        exception terminates with status ERRORED and records a traceback.
        """

    @classmethod
    def handle(cls, job: Job, *args: Any, **kwargs: Any) -> None:
        logger = logging.getLogger("peering.manager.jobs")

        try:
            job.start()
            cls(job).run(*args, **kwargs)
            job.terminate()
        except JobFailedError:
            logger.warning(f"Job {job} failed")
            job.terminate(status=JobStatus.FAILED)
        except Exception as e:
            tb_str = traceback.format_exc().replace(_INSTALL_ROOT, "")
            with contextlib.suppress(Exception):
                job.log(tb_str, level_choice=LogLevel.FAILURE, save=False)
            job.terminate(status=JobStatus.ERRORED, error=repr(e))
            if type(e) is JobTimeoutException:
                logger.error(e)
        finally:
            cls._reschedule(job, **kwargs)

    @classmethod
    def _reschedule(cls, job: Job, **kwargs: Any) -> None:
        if cls.scheduled_task_key and get_scheduled_task(cls.scheduled_task_key):
            # Catalog task: the live ScheduledTask row is the source of truth, so
            # reconciliation honours a disabled or re-timed row
            reconcile_task(cls.scheduled_task_key)
            return

        if not job.interval:
            return

        # Generic recurring job: self-reschedule from the dead job's interval.
        new_scheduled_time = max(
            (job.scheduled or job.started) + timedelta(minutes=job.interval),
            timezone.now() + timedelta(minutes=1),
        )
        cls.enqueue(
            instance=job.object,
            name=job.name,
            user=job.user,
            schedule_at=new_scheduled_time,
            interval=job.interval,
            **kwargs,
        )

    @classmethod
    def get_jobs(cls, instance=None):
        jobs = Job.objects.filter(name=cls.name)
        if instance is not None:
            object_type = ContentType.objects.get_for_model(instance, for_concrete_model=False)
            jobs = jobs.filter(object_type=object_type, object_id=instance.pk)
        return jobs

    @classmethod
    def enqueue(cls, *args: Any, **kwargs: Any) -> Job:
        name = kwargs.pop("name", None) or cls.name
        instance = kwargs.pop("instance", None)
        kwargs.setdefault("job_timeout", cls.job_timeout)
        return Job.enqueue(cls.handle, *args, name=name, object=instance, **kwargs)

    @classmethod
    @advisory_lock(ADVISORY_LOCK_KEYS["job-schedules"])
    def enqueue_once(cls, instance=None, schedule_at=None, interval=None, *args, **kwargs) -> Job:
        """
        Idempotent enqueue. If a row with matching params is already enqueued
        (PENDING/SCHEDULED/RUNNING), return it; otherwise replace and enqueue.
        Advisory-locked so concurrent worker starts can't both insert.
        """
        existing = cls.get_jobs(instance).filter(status__in=JobStatus.ENQUEUED_STATE_CHOICES).first()
        if existing:
            if (not schedule_at or existing.scheduled == schedule_at) and existing.interval == interval:
                return existing
            existing.delete()
        return cls.enqueue(
            *args,
            instance=instance,
            schedule_at=schedule_at,
            interval=interval,
            **kwargs,
        )
