from unittest.mock import MagicMock, patch

from django.test import TestCase
from django_rq.queues import DjangoRQ

__all__ = ("MockedQueueTestCase",)


class MockedQueueTestCase(TestCase):
    """Base case with the background queue mocked and exposed for assertions."""

    def setUp(self):
        super().setUp()
        patcher = patch("django_rq.get_queue")
        self.addCleanup(patcher.stop)
        self.queue = MagicMock(spec=DjangoRQ)
        patcher.start().return_value = self.queue
