from django.db import models


class JobResultStatus(models.TextChoices):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERRORED = "errored"
    FAILED = "failed"


class LogLevel(models.TextChoices):
    DEFAULT = "default"
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    FAILURE = "failure"
