import logging
import uuid
from datetime import timedelta
from unittest.mock import MagicMock

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from core.enums import JobStatus
from core.exceptions import JobFailedError
from core.models import Job
from core.tests.jobs_utils import MockedQueueTestCase
from peering_manager.jobs import JobLogHandler, JobRunner, system_job
from peering_manager.registry import SYSTEM_JOBS_KEY, registry


def _log_record(message, levelno=logging.INFO):
    return logging.makeLogRecord({"levelno": levelno, "msg": message})


class _SuccessRunner(JobRunner):
    class Meta:
        name = "test.success"

    def run(self, *args, **kwargs):
        type(self).called = True


class _FailureRunner(JobRunner):
    class Meta:
        name = "test.failure"

    def run(self, *args, **kwargs):
        raise RuntimeError("intentional failure")


class _HandledFailureRunner(JobRunner):
    class Meta:
        name = "test.handled_failure"

    def run(self, *args, **kwargs):
        raise JobFailedError("handled failure")


def _make_pending_job(name="test.success", interval=5, scheduled=None):
    """A scheduled job row, in the shape a runner receives."""
    return Job.objects.create(
        name=name,
        object_type=None,
        object_id=None,
        user=None,
        job_id=uuid.uuid4(),
        scheduled=scheduled or timezone.now(),
        interval=interval,
        status=JobStatus.SCHEDULED,
        queue_name="default",
    )


class JobRunnerLifecycleTests(MockedQueueTestCase):
    def test_success_marks_completed_and_reschedules(self):
        _SuccessRunner.called = False

        job = _make_pending_job(name="test.success", interval=10)
        with self.captureOnCommitCallbacks(execute=True):
            _SuccessRunner.handle(job)

        job.refresh_from_db()
        self.assertTrue(_SuccessRunner.called)
        self.assertEqual(job.status, JobStatus.COMPLETED)
        self.assertIsNotNone(job.completed)

        successor = Job.objects.filter(name="test.success").exclude(pk=job.pk).first()
        self.assertIsNotNone(successor, "expected a successor job to be enqueued")
        self.assertEqual(successor.interval, 10)
        self.assertEqual(successor.status, JobStatus.SCHEDULED)
        self.queue.enqueue_at.assert_called_once()

    def test_unhandled_exception_marks_errored_and_records_traceback(self):
        """An unhandled failure is recorded, not re-raised, and still reschedules."""
        job = _make_pending_job(name="test.failure", interval=5)

        _FailureRunner.handle(job)

        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.ERRORED)
        self.assertIn("intentional failure", job.error)
        # the traceback text is captured, not just a counter
        logged = " ".join(entry[-1] for entry in job.data["main"]["log"])
        self.assertIn("intentional failure", logged)
        self.assertIn("Traceback", logged)

        successor = Job.objects.filter(name="test.failure").exclude(pk=job.pk).first()
        self.assertIsNotNone(
            successor,
            "successor should still be enqueued so the schedule survives",
        )

    def test_jobfailed_marks_failed_not_errored(self):
        # a handled failure ends as failed, not errored
        job = _make_pending_job(name="test.handled_failure", interval=5)
        _HandledFailureRunner.handle(job)

        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.FAILED)

    def test_no_reschedule_when_interval_unset(self):
        job = _make_pending_job(name="test.success", interval=None, scheduled=None)
        _SuccessRunner.handle(job)

        siblings = Job.objects.filter(name="test.success").exclude(pk=job.pk).count()
        self.assertEqual(siblings, 0, "one-shot jobs should not re-enqueue")


class EnqueueOnceTests(MockedQueueTestCase):
    def test_creates_when_none_exists(self):
        result = _SuccessRunner.enqueue_once(interval=15)
        self.assertEqual(result.name, "test.success")
        self.assertEqual(result.interval, 15)
        # no scheduled time, so it runs as soon as possible
        self.assertEqual(result.status, JobStatus.PENDING)

    def test_returns_existing_when_interval_matches(self):
        first = _SuccessRunner.enqueue_once(interval=15)
        second = _SuccessRunner.enqueue_once(interval=15)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(
            Job.objects.filter(name="test.success", status__in=JobStatus.ENQUEUED_STATE_CHOICES).count(),
            1,
        )

    def test_replaces_when_interval_changes(self):
        first = _SuccessRunner.enqueue_once(interval=15)
        second = _SuccessRunner.enqueue_once(interval=60)
        self.assertNotEqual(first.pk, second.pk)
        self.assertFalse(Job.objects.filter(pk=first.pk).exists())
        self.assertEqual(second.interval, 60)


class JobLifecycleHelpersTests(TestCase):
    def test_start_is_idempotent(self):
        job = _make_pending_job()
        job.start()
        first_started = job.started
        # starting twice does not move the start time
        job.start()
        self.assertEqual(job.started, first_started)
        self.assertEqual(job.status, JobStatus.RUNNING)

    def test_terminate_records_error_and_status(self):
        job = _make_pending_job()
        job.start()
        job.terminate(status=JobStatus.ERRORED, error="boom")
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.ERRORED)
        self.assertEqual(job.error, "boom")
        self.assertIsNotNone(job.completed)

    def test_terminate_rejects_non_terminal_status(self):
        job = _make_pending_job()
        with self.assertRaises(ValidationError):
            job.terminate(status=JobStatus.RUNNING)


class JobLogHandlerTests(TestCase):
    def test_logger_output_is_batched_in_memory_without_per_line_save(self):
        job = _make_pending_job()
        handler = JobLogHandler(job)
        handler.emit(_log_record("first"))
        handler.emit(_log_record("second"))
        messages = [entry[-1] for entry in job.data["main"]["log"]]
        self.assertEqual(messages, ["first", "second"])
        # log lines accumulate in memory; the row is not written per line
        self.assertIsNone(Job.objects.get(pk=job.pk).data)

    def test_emit_is_a_noop_without_a_saved_job(self):
        # an absent or unsaved job is ignored, never written
        JobLogHandler(None).emit(_log_record("ignored"))
        unsaved = Job(name="test.unsaved", job_id=uuid.uuid4())
        JobLogHandler(unsaved).emit(_log_record("ignored"))
        self.assertIsNone(unsaved.data)


class JobEnqueueTests(MockedQueueTestCase):
    def test_schedule_at_sets_scheduled_status(self):
        scheduled_for = timezone.now() + timedelta(hours=1)

        with self.captureOnCommitCallbacks(execute=True):
            job = Job.enqueue(
                _SuccessRunner.handle,
                name="test.schedule",
                schedule_at=scheduled_for,
            )

        self.assertEqual(job.status, JobStatus.SCHEDULED)
        self.assertEqual(job.scheduled, scheduled_for)
        self.queue.enqueue_at.assert_called_once()

    def test_immediate_runs_synchronously(self):
        called = {"count": 0}

        def _func(*args, **kwargs):
            called["count"] += 1

        job = Job.enqueue(_func, name="test.immediate", immediate=True)
        self.assertEqual(called["count"], 1)
        self.assertEqual(job.status, JobStatus.PENDING)

    def test_schedule_at_and_immediate_are_mutually_exclusive(self):
        with self.assertRaises(ValueError):
            Job.enqueue(
                lambda **kw: None,
                name="bad",
                schedule_at=timezone.now(),
                immediate=True,
            )

    def test_redis_writes_skipped_on_rollback(self):
        """A rolled-back transaction enqueues nothing."""
        try:
            with transaction.atomic():
                _SuccessRunner.enqueue_once(interval=15)
                raise RuntimeError("simulate commit failure")
        except RuntimeError:
            pass

        self.queue.enqueue_at.assert_not_called()
        self.queue.enqueue.assert_not_called()
        self.assertEqual(Job.objects.filter(name="test.success").count(), 0)


class JobDeleteCancelsRqTests(MockedQueueTestCase):
    def test_delete_cancels_rq_job(self):
        rq_job = MagicMock()
        self.queue.fetch_job.return_value = rq_job

        job = _make_pending_job()
        rq_job_id = str(job.job_id)
        job.delete()

        self.queue.fetch_job.assert_called_with(rq_job_id)
        rq_job.cancel.assert_called_once()

    def test_delete_when_rq_job_missing_is_noop(self):
        # deletion stays quiet when the queue no longer tracks the job
        self.queue.fetch_job.return_value = None

        job = _make_pending_job()
        job.delete()


class SystemJobRegistryTests(TestCase):
    def test_decorator_validation_rejects_non_integer(self):
        with self.assertRaises(ImproperlyConfigured):

            @system_job(interval="daily")  # type: ignore[arg-type]
            class _Bad(JobRunner):
                class Meta:
                    name = "bad"

                def run(self, *args, **kwargs):
                    pass

    def test_v1_system_jobs_are_registered(self):
        """The built-in jobs register themselves in the catalog."""
        import core.system_jobs  # noqa: F401
        import peeringdb.jobs  # noqa: F401

        labels = {meta["label"] for meta in registry[SYSTEM_JOBS_KEY].values()}
        self.assertIn("Housekeeping", labels)
        self.assertIn("PeeringDB synchronisation", labels)
        self.assertIn("housekeeping", registry[SYSTEM_JOBS_KEY])
        self.assertIn("peeringdb-synchronisation", registry[SYSTEM_JOBS_KEY])
