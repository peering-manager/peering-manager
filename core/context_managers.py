from __future__ import annotations

import uuid
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.conf import settings

from extras.webhooks import flush_webhooks
from peering_manager.context import current_request, webhooks_queue

if TYPE_CHECKING:
    from collections.abc import Generator
    from contextlib import AbstractContextManager

    from django.http import HttpRequest

__all__ = ("SystemRequest", "change_logging", "system_change_logging")


@dataclass(frozen=True)
class SystemRequest:
    """
    Stands in for an HTTP request when a system job or a command changes objects, so the change log record these
    changes under the `SYSTEM_USER_NAME` author.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user: None = field(default=None, init=False)


@contextmanager
def change_logging(request: HttpRequest | SystemRequest) -> Generator[None]:
    """
    Enables change logging by connecting the appropriate signals to their receivers before code is run, and
    disconnecting them afterward.
    """
    current_request.set(request)
    webhooks_queue.set([])

    try:
        yield
        flush_webhooks(webhooks_queue.get())
    finally:
        # A worker that does not fork runs the next job in this context, which must not record changes for this one
        current_request.set(None)
        webhooks_queue.set([])


def system_change_logging() -> AbstractContextManager[None]:
    """
    Records the changes of a system job or a command under the system user, only when `CHANGELOG_SYSTEM_CHANGES` is
    enabled.
    """
    if settings.CHANGELOG_SYSTEM_CHANGES:
        return change_logging(SystemRequest())
    return nullcontext()
