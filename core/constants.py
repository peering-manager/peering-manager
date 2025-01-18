from dataclasses import dataclass

from rq.job import JobStatus

__all__ = (
    "CENSORSHIP_STRING",
    "CENSORSHIP_STRING_CHANGED",
    "GIT_ERROR_MATCHES",
    "RQ_TASK_STATUSES",
)

CENSORSHIP_STRING = "*************"
CENSORSHIP_STRING_CHANGED = "***CHANGED***"


@dataclass
class Status:
    label: str
    colour: str


RQ_TASK_STATUSES = {
    JobStatus.QUEUED: Status("Queued", "info"),
    JobStatus.FINISHED: Status("Finished", "success"),
    JobStatus.FAILED: Status("Failed", "danger"),
    JobStatus.STARTED: Status("Started", "primary"),
    JobStatus.DEFERRED: Status("Deferred", "warning"),
    JobStatus.SCHEDULED: Status("Scheduled", "info"),
    JobStatus.STOPPED: Status("Stopped", "danger"),
    JobStatus.CANCELED: Status("Cancelled", "warning"),
}

GIT_ERROR_MATCHES = (
    # GitHub
    "push declined due to repository rule violations",
    # GitLab
    "not allowed to push code to protected branches",
)
