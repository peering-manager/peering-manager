from django.db import models

WEBHOOK_HTTP_CONTENT_TYPE_JSON = "application/json"


class HttpMethod(models.TextChoices):
    GET = "GET", "GET"
    POST = "POST", "POST"
    PUT = "PUT", "PUT"
    PATCH = "PATCH", "PATCH"
    DELETE = "DELETE", "DELETE"


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
