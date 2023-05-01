from utils.enums import ChoiceSet


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
