import sys
import traceback
import uuid
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone
from rq.exceptions import AbandonedJobError

from core.enums import JobStatus
from core.exceptions import exception_handler
from core.models import Job


class ExceptionHandlerTest(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            name="test.job",
            job_id=uuid.uuid4(),
            scheduled=timezone.now(),
            status=JobStatus.RUNNING,
            queue_name="default",
        )
        self.rq_job = SimpleNamespace(id=str(self.job.job_id))

    def test_a_raised_exception_is_recorded(self):
        try:
            raise RuntimeError("intentional failure")
        except RuntimeError:
            exception_handler(self.rq_job, *sys.exc_info())

        self.job.refresh_from_db()
        self.assertEqual(JobStatus.ERRORED, self.job.status)
        self.assertIn("RuntimeError: intentional failure", self.job.output)

    def test_an_abandoned_job_is_recorded(self):
        # RQ passes a stack summary, not a traceback, when it cleans up an abandoned job
        exception_handler(self.rq_job, AbandonedJobError, AbandonedJobError(), traceback.extract_stack())

        self.job.refresh_from_db()
        self.assertEqual(JobStatus.ERRORED, self.job.status)
        self.assertIn("AbandonedJobError", self.job.output)

    def test_a_job_without_record_is_skipped(self):
        with self.assertLogs("peering.manager.core.jobs", level="ERROR"):
            exception_handler(SimpleNamespace(id=str(uuid.uuid4())), AbandonedJobError, AbandonedJobError(), None)

        self.job.refresh_from_db()
        self.assertEqual(JobStatus.RUNNING, self.job.status)
