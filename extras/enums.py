from curses.ascii import DEL

from django.db import models

from utils.enums import ChoiceSet

WEBHOOK_HTTP_CONTENT_TYPE_JSON = "application/json"

EXTRAS_FEATURES = ("config-contexts", "export-templates", "tags")


class HttpMethod(ChoiceSet):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

    CHOICES = (
        (GET, "GET"),
        (POST, "POST"),
        (PUT, "PUT"),
        (PATCH, "PATCH"),
        (DELETE, "DELETE"),
    )


class JobResultStatus(ChoiceSet):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERRORED = "errored"
    FAILED = "failed"

    CHOICES = (
        (PENDING, "Pending", "primary"),
        (RUNNING, "Running", "warning"),
        (COMPLETED, "Completed", "success"),
        (ERRORED, "Errored", "danger"),
        (FAILED, "Failed", "danger"),
    )


class LogLevel(ChoiceSet):
    DEFAULT = "default"
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    FAILURE = "failure"

    CHOICES = (
        (DEFAULT, "default", "primary"),
        (SUCCESS, "success", "success"),
        (INFO, "info", "info"),
        (WARNING, "warning", "warning"),
        (FAILURE, "failure", "danger"),
    )
