from __future__ import annotations

import contextlib
import logging
import uuid
from collections import OrderedDict
from functools import partial

import django_rq
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from rq.exceptions import InvalidJobOperation

from ..enums import JobStatus, LogLevel

__all__ = ("Job",)


class Job(models.Model):
    """
    Tracks the lifecycle of a job which represents a background task (e.g. a
    configuration push).
    """

    object_type = models.ForeignKey(
        to=ContentType,
        related_name="jobs",
        verbose_name="Object type",
        help_text="The object type to which this job applies",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    object_id = models.PositiveBigIntegerField(blank=True, null=True)
    object = GenericForeignKey(ct_field="object_type", fk_field="object_id", for_concrete_model=False)
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    scheduled = models.DateTimeField(blank=True, null=True)
    interval = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=(MinValueValidator(1),),
        help_text="Recurrence interval (in minutes)",
    )
    started = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, related_name="+", null=True, blank=True)
    status = models.CharField(max_length=30, choices=JobStatus, default=JobStatus.PENDING)
    data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    error = models.TextField(editable=False, blank=True)
    job_id = models.UUIDField(unique=True)
    queue_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the queue in which this job was enqueued",
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return str(self.job_id)

    def get_absolute_url(self) -> str:
        return reverse("core:job", args=[self.pk])

    def delete(self, *args, **kwargs):
        rq_queue_name = self.queue_name or "default"
        rq_job_id = str(self.job_id)

        super().delete(*args, **kwargs)

        queue = django_rq.get_queue(rq_queue_name)
        job = queue.fetch_job(rq_job_id)
        if job:
            with contextlib.suppress(InvalidJobOperation):
                job.cancel()

    @classmethod
    def enqueue(
        cls,
        func,
        *args,
        name="",
        object=None,
        object_model=None,
        user=None,
        schedule_at=None,
        interval=None,
        immediate=False,
        queue_name=None,
        job_timeout=None,
        **kwargs,
    ) -> Job:
        """
        The RQ side is deferred via `transaction.on_commit` so a PG rollback
        can't leave Redis ahead of the database.
        """
        if schedule_at and immediate:
            raise ValueError("enqueue() cannot be called with values for both schedule_at and immediate.")

        target = object_model or object
        object_type = (
            ContentType.objects.get_for_model(target, for_concrete_model=False) if target is not None else None
        )
        rq_queue_name = queue_name or "default"

        status = JobStatus.SCHEDULED if schedule_at else JobStatus.PENDING
        job = cls.objects.create(
            name=name,
            object_type=object_type,
            object_id=object.pk if object else None,
            user=user,
            job_id=uuid.uuid4(),
            scheduled=schedule_at,
            interval=interval,
            status=status,
            queue_name=rq_queue_name,
        )

        job_kwargs = {"job_id": str(job.job_id), "job": job, **kwargs}
        rq_options = {}
        if job_timeout is not None:
            rq_options["job_timeout"] = job_timeout

        if immediate:
            func(*args, **job_kwargs)
        elif schedule_at:
            queue = django_rq.get_queue(rq_queue_name)
            callback = partial(
                queue.enqueue_at,
                schedule_at,
                func,
                *args,
                **job_kwargs,
                **rq_options,
            )
            transaction.on_commit(callback)
        elif hasattr(func, "delay"):
            # @job-decorated callable: timeout comes from the decorator
            callback = partial(func.delay, *args, **job_kwargs)
            transaction.on_commit(callback)
        else:
            queue = django_rq.get_queue(rq_queue_name)
            callback = partial(queue.enqueue, func, *args, **job_kwargs, **rq_options)
            transaction.on_commit(callback)

        return job

    @staticmethod
    def _data_grouping_struct():
        return OrderedDict([("success", 0), ("info", 0), ("warning", 0), ("failure", 0), ("log", [])])

    @property
    def output(self) -> str:
        if not self.data or "output" not in self.data or not self.data["output"]:
            return ""

        lines = []
        for line in self.data["output"]["log"]:
            lines.append(line[-1])

        return "\n".join(lines)

    @property
    def duration(self) -> str:
        if not self.completed:
            return ""

        start_time = self.started or self.created
        if not start_time:
            return ""

        duration = self.completed - start_time
        minutes, seconds = divmod(duration.total_seconds(), 60)

        return f"{int(minutes)} minutes, {seconds:.2f} seconds"

    @property
    def is_over(self) -> bool:
        return self.status in JobStatus.TERMINAL_STATE_CHOICES

    def get_status_colour(self):
        return JobStatus.colours.get(self.status)

    def start(self):
        if self.started is not None:
            return
        self.started = timezone.now()
        self.status = JobStatus.RUNNING
        self.save()

    start.alters_data = True

    def terminate(self, status=JobStatus.COMPLETED, error=None):
        if status not in JobStatus.TERMINAL_STATE_CHOICES:
            raise ValidationError(
                f"Invalid status for job termination: {status}. Choices: {', '.join(JobStatus.TERMINAL_STATE_CHOICES)}"
            )
        self.status = status
        if error:
            self.error = error
        self.completed = timezone.now()
        self.save()

    terminate.alters_data = True

    def log(
        self,
        message,
        object=None,
        level_choice=LogLevel.DEFAULT,
        grouping="main",
        logger=None,
        save=True,
    ):
        if level_choice not in LogLevel.values():
            raise Exception(f"Unknown logging level: {level_choice}")

        if not self.data:
            self.data = {}

        data = self.data
        data.setdefault(grouping, self._data_grouping_struct())
        if "log" not in data[grouping]:
            data[grouping]["log"] = []
        log = data[grouping]["log"]

        log.append(
            [
                timezone.now().isoformat(),
                level_choice,
                str(object) if object else None,
                (object.get_absolute_url() if hasattr(object, "get_absolute_url") else None),
                str(message),
            ]
        )

        if level_choice != LogLevel.DEFAULT:
            data[grouping].setdefault(level_choice, 0)
            data[grouping][level_choice] += 1
            if "total" not in data:
                data["total"] = self._data_grouping_struct()
                del data["total"]["log"]
            data["total"].setdefault(level_choice, 0)
            data["total"][level_choice] += 1

        if logger:
            if level_choice == LogLevel.FAILURE:
                log_level = logging.ERROR
            elif level_choice == LogLevel.WARNING:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
            logger.log(log_level, str(message))

        if save:
            self.save()

    def log_warning(self, message, object=None, grouping="main", logger=None, save=True):
        self.log(
            message,
            object=object,
            level_choice=LogLevel.WARNING,
            grouping=grouping,
            logger=logger,
            save=save,
        )

    def mark_completed(self, log_message, object=None, logger=None):
        self.log(
            log_message,
            object=object,
            level_choice=LogLevel.SUCCESS,
            logger=logger,
            save=False,
        )
        self.terminate(status=JobStatus.COMPLETED)

    def mark_errored(self, log_message, object=None, logger=None):
        self.log(
            log_message,
            object=object,
            level_choice=LogLevel.FAILURE,
            logger=logger,
            save=False,
        )
        self.terminate(status=JobStatus.ERRORED, error=str(log_message))

    def mark_failed(self, log_message, object=None, logger=None):
        self.log(
            log_message,
            object=object,
            level_choice=LogLevel.FAILURE,
            logger=logger,
            save=False,
        )
        self.terminate(status=JobStatus.FAILED, error=str(log_message))

    def mark_running(self, log_message, object=None, logger=None):
        self.log(
            log_message,
            object=object,
            level_choice=LogLevel.INFO,
            logger=logger,
            save=False,
        )
        self.start()

    def set_output(self, output, object=None):
        self.log(
            output,
            object=object,
            level_choice=LogLevel.DEFAULT,
            grouping="output",
            save=False,
        )
