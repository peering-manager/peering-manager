from rest_framework import status
from rest_framework.exceptions import APIException

__all__ = ("AbortException", "RQWorkerNotRunningException")


class AbortRequest(Exception):
    """
    Raised to cleanly abort a request (for example, by a pre_save signal receiver).
    """

    def __init__(self, message):
        self.message = message


class RQWorkerNotRunningException(APIException):
    """
    Indicates the temporary inability to enqueue a new task because no RQ worker
    processes are currently running.
    """

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Unable to process request: RQ worker process not running."
    default_code = "rq_worker_not_running"
