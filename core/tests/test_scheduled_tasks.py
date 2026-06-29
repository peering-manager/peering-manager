import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.enums import JobInterval, JobStatus
from core.models import Job, ScheduledTask
from core.scheduling import reconcile_schedules, run_now
from core.tests.jobs_utils import MockedQueueTestCase
from peering_manager.jobs import JobRunner, system_job
from peering_manager.registry import SYSTEM_JOBS_KEY, registry

TASK_KEY = "test-scheduled-task"
TASK_LABEL = "Test scheduled task"


class _ScheduledRunner(JobRunner):
    class Meta:
        name = TASK_LABEL

    def run(self, *args, **kwargs):
        pass


def setUpModule():
    # register only for this module so the catalog stays clean elsewhere
    system_job(
        interval=JobInterval.DAILY,
        key=TASK_KEY,
        label=TASK_LABEL,
        min_interval=JobInterval.HOURLY,
    )(_ScheduledRunner)


def tearDownModule():
    registry[SYSTEM_JOBS_KEY].pop(TASK_KEY, None)
    _ScheduledRunner.scheduled_task_key = None


def _make_task(enabled=True, interval=JobInterval.DAILY):
    return ScheduledTask.objects.create(task=TASK_KEY, enabled=enabled, interval=interval)


def _make_job(status, *, scheduled=None, started=None, completed=None, interval=None):
    return Job.objects.create(
        name=TASK_LABEL,
        job_id=uuid.uuid4(),
        status=status,
        scheduled=scheduled,
        started=started,
        completed=completed,
        interval=interval or JobInterval.DAILY,
        queue_name="default",
    )


class ScheduledTaskModelTests(TestCase):
    def test_clean_rejects_unknown_task(self):
        task = ScheduledTask(task="does-not-exist", enabled=True, interval=1440)
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_clean_rejects_interval_below_minimum(self):
        # below the task's allowed minimum
        task = ScheduledTask(task=TASK_KEY, enabled=True, interval=5)
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_clean_accepts_valid_task(self):
        task = ScheduledTask(task=TASK_KEY, enabled=True, interval=JobInterval.DAILY)
        task.full_clean()  # must not raise

    def test_label_falls_back_to_key_for_unknown(self):
        self.assertEqual(ScheduledTask(task=TASK_KEY).task_label, TASK_LABEL)
        self.assertEqual(ScheduledTask(task="mystery").task_label, "mystery")


class ScheduledTaskPropertyTests(TestCase):
    def setUp(self):
        self.task = _make_task()

    def test_last_job_is_most_recent_terminal_run(self):
        # created out of completion order, so a wrong sort or a missing
        # terminal-only filter would pick the wrong row
        newest = _make_job(JobStatus.COMPLETED, completed=timezone.now())
        _make_job(JobStatus.COMPLETED, completed=timezone.now() - timedelta(hours=2))
        _make_job(JobStatus.RUNNING, started=timezone.now())
        _make_job(JobStatus.SCHEDULED, scheduled=timezone.now() + timedelta(hours=1))
        self.assertEqual(self.task.last_job.pk, newest.pk)

    def test_last_job_is_none_without_a_terminal_run(self):
        _make_job(JobStatus.SCHEDULED, scheduled=timezone.now() + timedelta(hours=1))
        self.assertIsNone(self.task.last_job)

    def test_next_run_returns_soonest_scheduled(self):
        _make_job(JobStatus.SCHEDULED, scheduled=timezone.now() + timedelta(hours=2))
        sooner = _make_job(JobStatus.SCHEDULED, scheduled=timezone.now() + timedelta(hours=1))
        self.assertEqual(self.task.next_run, sooner.scheduled)

    def test_next_run_prefers_run_now_pending_job(self):
        # a run-now job is imminent and wins over a future one
        _make_job(JobStatus.SCHEDULED, scheduled=timezone.now() + timedelta(hours=1))
        _make_job(JobStatus.PENDING, scheduled=None)
        self.assertIsNone(self.task.next_run)


class ReconcileTests(MockedQueueTestCase):
    def test_seeds_missing_rows_from_catalog(self):
        reconcile_schedules()
        row = ScheduledTask.objects.get(task=TASK_KEY)
        self.assertTrue(row.enabled)
        self.assertEqual(row.interval, JobInterval.DAILY)

    def test_enabled_row_is_enqueued(self):
        _make_task(enabled=True)
        reconcile_schedules()
        self.assertTrue(Job.objects.filter(name=TASK_LABEL, status__in=JobStatus.ENQUEUED_STATE_CHOICES).exists())

    def test_disabled_row_cancels_pending_jobs(self):
        _make_task(enabled=False)
        _make_job(JobStatus.SCHEDULED, scheduled=timezone.now())
        reconcile_schedules()
        self.assertFalse(
            Job.objects.filter(name=TASK_LABEL, status__in=(JobStatus.PENDING, JobStatus.SCHEDULED)).exists()
        )

    def test_disabled_row_leaves_running_job_alone(self):
        _make_task(enabled=False)
        running = _make_job(JobStatus.RUNNING, started=timezone.now())
        reconcile_schedules()
        self.assertTrue(Job.objects.filter(pk=running.pk).exists())

    def test_unknown_task_row_is_skipped(self):
        # a row with no matching catalog entry is tolerated, not fatal
        ScheduledTask.objects.create(task="ghost-task", enabled=True, interval=JobInterval.DAILY)
        reconcile_schedules()  # must not raise
        self.assertTrue(ScheduledTask.objects.filter(task="ghost-task").exists())


class HandleRescheduleTests(MockedQueueTestCase):
    def test_disabled_row_stops_the_chain(self):
        _make_task(enabled=False)
        job = _make_job(JobStatus.SCHEDULED, scheduled=timezone.now())
        _ScheduledRunner.handle(job)
        self.assertFalse(
            Job.objects.filter(name=TASK_LABEL)
            .exclude(pk=job.pk)
            .filter(status__in=JobStatus.ENQUEUED_STATE_CHOICES)
            .exists()
        )

    def test_reschedules_at_current_row_interval(self):
        _make_task(enabled=True, interval=JobInterval.HOURLY)
        # successor takes the row interval, not the job's stale one
        job = _make_job(JobStatus.SCHEDULED, scheduled=timezone.now(), interval=JobInterval.DAILY)
        _ScheduledRunner.handle(job)
        successor = Job.objects.filter(name=TASK_LABEL).exclude(pk=job.pk).first()
        self.assertIsNotNone(successor)
        self.assertEqual(successor.interval, JobInterval.HOURLY)
        self.assertEqual(successor.status, JobStatus.SCHEDULED)


class SignalTests(MockedQueueTestCase):
    def test_save_triggers_reconcile(self):
        with self.captureOnCommitCallbacks(execute=True):
            _make_task(enabled=True, interval=JobInterval.HOURLY)
        self.assertTrue(Job.objects.filter(name=TASK_LABEL, status__in=JobStatus.ENQUEUED_STATE_CHOICES).exists())

    def test_delete_triggers_reconcile_and_cancels(self):
        with self.captureOnCommitCallbacks(execute=True):
            task = _make_task(enabled=True, interval=JobInterval.HOURLY)
        with self.captureOnCommitCallbacks(execute=True):
            task.delete()
        self.assertFalse(
            Job.objects.filter(name=TASK_LABEL, status__in=(JobStatus.PENDING, JobStatus.SCHEDULED)).exists()
        )


class RunNowTests(MockedQueueTestCase):
    def test_clears_stuck_run_and_queues_an_immediate_one(self):
        _make_task(enabled=True)
        stuck = _make_job(JobStatus.RUNNING, started=timezone.now() - timedelta(days=2))
        run_now(TASK_KEY)
        self.assertFalse(Job.objects.filter(pk=stuck.pk).exists())
        fresh = Job.objects.filter(name=TASK_LABEL).first()
        self.assertIsNotNone(fresh)
        self.assertEqual(fresh.status, JobStatus.PENDING)


class ScheduledTaskViewTests(MockedQueueTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(username="admin", email="admin@example.net", password="password")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_list_view(self):
        _make_task()
        response = self.client.get(reverse("core:scheduledtask_list"))
        self.assertContains(response, TASK_LABEL)

    def test_detail_view(self):
        task = _make_task()
        response = self.client.get(reverse("core:scheduledtask", args=[task.pk]))
        self.assertContains(response, TASK_LABEL)

    def test_add_view_get(self):
        response = self.client.get(reverse("core:scheduledtask_add"))
        self.assertEqual(response.status_code, 200)

    def test_create_schedules_the_task(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("core:scheduledtask_add"),
                data={
                    "task": TASK_KEY,
                    "enabled": "on",
                    "interval": JobInterval.DAILY,
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ScheduledTask.objects.filter(task=TASK_KEY).exists())
        self.assertTrue(Job.objects.filter(name=TASK_LABEL, status__in=JobStatus.ENQUEUED_STATE_CHOICES).exists())

    def test_run_now_recovers_a_stuck_task(self):
        task = _make_task(enabled=True)
        stuck = _make_job(JobStatus.RUNNING, started=timezone.now() - timedelta(days=2))
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("core:scheduledtask_run", args=[task.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Job.objects.filter(pk=stuck.pk).exists())
        self.assertTrue(Job.objects.filter(name=TASK_LABEL, status__in=JobStatus.ENQUEUED_STATE_CHOICES).exists())
