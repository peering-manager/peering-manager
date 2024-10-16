from utils.enums import ChoiceSet


class DataSourceStatus(ChoiceSet):
    NEW = "new"
    QUEUED = "queued"
    SYNCHRONISING = "synchronising"
    PUSHING = "pushing"
    COMPLETED = "completed"
    FAILED = "failed"

    CHOICES = (
        (NEW, "New", "primary"),
        (QUEUED, "Queued", "secondary"),
        (SYNCHRONISING, "Synchronising", "warning"),
        (PUSHING, "Pushing", "warning"),
        (COMPLETED, "Completed", "success"),
        (FAILED, "Failed", "danger"),
    )


class JobStatus(ChoiceSet):
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


class ObjectChangeAction(ChoiceSet):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

    CHOICES = (
        (CREATE, "Created", "success"),
        (UPDATE, "Updated", "warning"),
        (DELETE, "Deleted", "danger"),
    )
