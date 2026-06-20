from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from peering_manager.models import ChangeLoggedModel
from peering_manager.registry import SYSTEM_JOBS_KEY, registry

from ..enums import JobStatus
from .jobs import Job

__all__ = ("ScheduledTask",)


class ScheduledTask(ChangeLoggedModel):
    """
    User-configurable schedule for a registered system job. The set of valid `task`
    values is the catalog declared with `@system_job`.
    """

    task = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=True)
    interval = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Recurrence interval (in minutes)",
    )

    class Meta:
        ordering = ["task"]

    def __str__(self) -> str:
        return self.task_label

    def get_absolute_url(self) -> str:
        return reverse("core:scheduledtask", args=[self.pk])

    @property
    def _meta_entry(self) -> dict | None:
        return registry[SYSTEM_JOBS_KEY].get(self.task)

    @property
    def is_known(self) -> bool:
        return self._meta_entry is not None

    @property
    def runner(self):
        entry = self._meta_entry
        return entry["cls"] if entry else None

    @property
    def task_label(self) -> str:
        entry = self._meta_entry
        return entry["label"] if entry else self.task

    @property
    def last_job(self) -> Job | None:
        runner = self.runner
        if runner is None:
            return None
        return (
            Job.objects.filter(
                name=runner.name,
                status__in=JobStatus.TERMINAL_STATE_CHOICES,
            )
            .order_by("-completed")
            .first()
        )

    @property
    def next_run(self):
        runner = self.runner
        if runner is None:
            return None
        job = (
            Job.objects.filter(
                name=runner.name,
                status__in=(JobStatus.PENDING, JobStatus.SCHEDULED),
            )
            .order_by("scheduled")
            .first()
        )
        return job.scheduled if job else None

    def clean(self) -> None:
        super().clean()

        entry = self._meta_entry
        if entry is None:
            raise ValidationError({"task": f"Unknown task: {self.task}"})

        min_interval = entry["min_interval"]
        if self.interval < min_interval:
            raise ValidationError(
                {
                    "interval": f"{self.task_label} cannot run more often than every {min_interval} minutes."
                }
            )
