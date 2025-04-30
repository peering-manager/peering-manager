from __future__ import annotations

import logging
import uuid
from collections import OrderedDict

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.urls import reverse
from django.utils import timezone

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
    )
    object_id = models.PositiveBigIntegerField(blank=True, null=True)
    object = GenericForeignKey(
        ct_field="object_type", fk_field="object_id", for_concrete_model=False
    )
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, related_name="+", null=True, blank=True
    )
    status = models.CharField(
        max_length=30, choices=JobStatus, default=JobStatus.PENDING
    )
    data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    job_id = models.UUIDField(unique=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return str(self.job_id)

    def get_absolute_url(self) -> str:
        return reverse("core:job", args=[self.pk])

    @classmethod
    def enqueue(
        cls, func, *args, name="", object=None, object_model=None, user=None, **kwargs
    ) -> Job:
        """
        Creates a Job instance and enqueue it using the given callable.
        """
        job = cls.objects.create(
            name=name,
            object_type=ContentType.objects.get_for_model(
                object_model or object, for_concrete_model=False
            ),
            object_id=object.pk if object else None,
            user=user,
            job_id=uuid.uuid4(),
        )
        func.delay(*args, job_id=str(job.job_id), job=job, **kwargs)

        return job

    @staticmethod
    def _data_grouping_struct():
        return OrderedDict(
            [("success", 0), ("info", 0), ("warning", 0), ("failure", 0), ("log", [])]
        )

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
        return self.status in [JobStatus.COMPLETED, JobStatus.ERRORED, JobStatus.FAILED]

    def get_status_colour(self):
        return JobStatus.colours.get(self.status)

    def set_status(self, status):
        """
        Helper method to change the status of the job. If the target status is
        terminal, the completion time is also set.
        """
        self.status = status
        if status == JobStatus.RUNNING:
            self.started = timezone.now()
        if status in [JobStatus.COMPLETED, JobStatus.ERRORED, JobStatus.FAILED]:
            self.completed = timezone.now()

    def log(
        self,
        message,
        object=None,
        level_choice=LogLevel.DEFAULT,
        grouping="main",
        logger=None,
        save=True,
    ):
        """
        Stores log messages in job's `data` field.
        """
        if level_choice not in LogLevel.values():
            raise Exception(f"Unknown logging level: {level_choice}")

        if not self.data:
            self.data = {}

        data = self.data
        data.setdefault(grouping, self._data_grouping_struct())
        # Just in case it got initialized by something else:
        if "log" not in data[grouping]:
            data[grouping]["log"] = []
        log = data[grouping]["log"]

        # Record the log message
        log.append(
            [
                timezone.now().isoformat(),
                level_choice,
                str(object) if object else None,
                (
                    object.get_absolute_url()
                    if hasattr(object, "get_absolute_url")
                    else None
                ),
                str(message),
            ]
        )

        # Default log messages have no status and do not get counted
        if level_choice != LogLevel.DEFAULT:
            # Update per-grouping and total results counters
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

    def log_warning(
        self, message, object=None, grouping="main", logger=None, save=True
    ):
        self.log(
            message,
            object=object,
            level_choice=LogLevel.WARNING,
            grouping=grouping,
            logger=logger,
            save=save,
        )

    def mark_completed(self, log_message, object=None, logger=None):
        self.set_status(JobStatus.COMPLETED)
        self.log(
            log_message, object=object, level_choice=LogLevel.SUCCESS, logger=logger
        )

    def mark_errored(self, log_message, object=None, logger=None):
        self.set_status(JobStatus.ERRORED)
        self.log(
            log_message, object=object, level_choice=LogLevel.FAILURE, logger=logger
        )

    def mark_failed(self, log_message, object=None, logger=None):
        self.set_status(JobStatus.FAILED)
        self.log(
            log_message, object=object, level_choice=LogLevel.FAILURE, logger=logger
        )

    def mark_running(self, log_message, object=None, logger=None):
        self.set_status(JobStatus.RUNNING)
        self.log(log_message, object=object, level_choice=LogLevel.INFO, logger=logger)

    def set_output(self, output, object=None):
        self.log(
            output,
            object=object,
            level_choice=LogLevel.DEFAULT,
            grouping="output",
            save=False,
        )
