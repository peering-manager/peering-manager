import uuid

import django_rq
from django.test import TestCase
from rq.registry import StartedJobRegistry

from core.enums import JobStatus
from core.exceptions import exception_handler
from core.models import Job


class ExceptionHandlerTest(TestCase):
    def test_abandoned_jobs(self):
        queue = django_rq.get_queue("default")
        registry = StartedJobRegistry(queue=queue)
        job = Job.objects.create(job_id=uuid.uuid4())

        for job_id in (str(job.job_id), str(uuid.uuid4())):
            rq_job = queue.create_job(print, job_id=job_id)
            rq_job.save()
            self.addCleanup(rq_job.delete)
            queue.connection.zadd(registry.key, {f"{job_id}:0": 0})

        registry.cleanup(timestamp=0, exception_handlers=[exception_handler])

        job.refresh_from_db()
        self.assertEqual(JobStatus.ERRORED, job.status)
        self.assertIn("AbandonedJobError", job.output)
