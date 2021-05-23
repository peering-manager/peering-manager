import logging
import uuid
from collections import OrderedDict

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .enums import JobResultStatus, LogLevel


class JobResult(models.Model):
    """
    This model stores the results for a job that has been run in background.
    """

    name = models.CharField(max_length=255)
    obj_type = models.ForeignKey(
        to=ContentType,
        related_name="job_results",
        verbose_name="Object type",
        help_text="The object type to which this job result applies",
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, related_name="+", null=True, blank=True
    )
    status = models.CharField(
        max_length=30,
        choices=JobResultStatus.choices,
        default=JobResultStatus.PENDING,
    )
    data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    job_id = models.UUIDField(unique=True)

    class Meta:
        ordering = ["-created"]

    @classmethod
    def enqueue_job(cls, func, name, obj_type, user, *args, **kwargs):
        """
        Creates a JobResult instance and enqueue a job using the given callable.
        """
        job_result = cls.objects.create(
            name=name,
            obj_type=ContentType.objects.get_for_model(obj_type),
            user=user,
            job_id=uuid.uuid4(),
        )

        func.delay(
            *args, job_id=str(job_result.job_id), job_result=job_result, **kwargs
        )

        return job_result

    @staticmethod
    def _data_grouping_struct():
        return OrderedDict(
            [("success", 0), ("info", 0), ("warning", 0), ("failure", 0), ("log", [])]
        )

    @property
    def output(self):
        if not self.data or "output" not in self.data or not self.data["output"]:
            return ""

        lines = []
        for line in self.data["output"]["log"]:
            lines.append(line[-1])

        return "\n".join(lines)

    @property
    def duration(self):
        if not self.completed:
            return ""

        duration = self.completed - self.created
        minutes, seconds = divmod(duration.total_seconds(), 60)

        return f"{int(minutes)} minutes, {seconds:.2f} seconds"

    @property
    def is_over(self):
        return self.status in [
            JobResultStatus.COMPLETED,
            JobResultStatus.ERRORED,
            JobResultStatus.FAILED,
        ]

    def __str__(self):
        return f"Result for job {self.job_id}"

    def get_absolute_url(self):
        return reverse("extras:jobresult_details", args=[self.pk])

    def set_status(self, status):
        """
        Helper method to change the status of the job result. If the target status is
        terminal, the completion time is also set.
        """
        self.status = status
        if status in [
            JobResultStatus.COMPLETED,
            JobResultStatus.ERRORED,
            JobResultStatus.FAILED,
        ]:
            self.completed = timezone.now()

    def log(
        self,
        message,
        obj=None,
        level_choice=LogLevel.DEFAULT,
        grouping="main",
        logger=None,
        save=True,
    ):
        """
        Stores log messages in a JobResult's `data` field.
        """
        if level_choice not in LogLevel.values:
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
                str(obj) if obj else None,
                obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else None,
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

    def mark_completed(self, log_message, obj=None, logger=None):
        self.set_status(JobResultStatus.COMPLETED)
        self.log(log_message, obj=obj, level_choice=LogLevel.SUCCESS, logger=logger)

    def mark_errored(self, log_message, obj=None, logger=None):
        self.set_status(JobResultStatus.ERRORED)
        self.log(log_message, obj=obj, level_choice=LogLevel.FAILURE, logger=logger)

    def mark_failed(self, log_message, obj=None, logger=None):
        self.set_status(JobResultStatus.FAILED)
        self.log(log_message, obj=obj, level_choice=LogLevel.FAILURE, logger=logger)

    def mark_running(self, log_message, obj=None, logger=None):
        self.set_status(JobResultStatus.RUNNING)
        self.log(log_message, obj=obj, level_choice=LogLevel.INFO, logger=logger)

    def set_output(self, output, obj=None):
        self.log(
            output,
            obj=obj,
            level_choice=LogLevel.DEFAULT,
            grouping="output",
            save=False,
        )
