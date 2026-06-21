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
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    ERRORED = "errored"
    FAILED = "failed"

    CHOICES = (
        (PENDING, "Pending", "primary"),
        (SCHEDULED, "Scheduled", "secondary"),
        (RUNNING, "Running", "warning"),
        (COMPLETED, "Completed", "success"),
        (ERRORED, "Errored", "danger"),
        (FAILED, "Failed", "danger"),
    )

    ENQUEUED_STATE_CHOICES = (PENDING, SCHEDULED, RUNNING)
    TERMINAL_STATE_CHOICES = (COMPLETED, ERRORED, FAILED)


class JobInterval(ChoiceSet):
    """
    Predefined recurrence intervals (in minutes) for periodic jobs.
    """

    MINUTELY = 1
    HOURLY = 60
    HALF_DAILY = 60 * 12
    DAILY = 60 * 24
    WEEKLY = 60 * 24 * 7
    MONTHLY = 60 * 24 * 30

    CHOICES = (
        (MINUTELY, "Every minute"),
        (HOURLY, "Hourly"),
        (HALF_DAILY, "Every 12 hours"),
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (MONTHLY, "Every 30 days"),
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
