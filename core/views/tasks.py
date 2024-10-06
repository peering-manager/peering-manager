import contextlib

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import render
from django.views.generic import View
from django_rq.queues import get_queue_by_index, get_redis_connection
from django_rq.settings import QUEUES_LIST, QUEUES_MAP
from django_rq.utils import get_jobs, get_statistics
from rq import Worker
from rq.exceptions import NoSuchJobError
from rq.job import Job as RQ_Job
from rq.job import JobStatus
from rq.registry import (
    DeferredJobRegistry,
    FailedJobRegistry,
    FinishedJobRegistry,
    ScheduledJobRegistry,
    StartedJobRegistry,
)
from rq.worker_registration import clean_worker_registry

from peering_manager.views.generic.mixins import TableMixin

from .. import tables

__all__ = (
    "BackgroundQueueListView",
    "BackgroundTaskListView",
    "BackgroundTaskView",
    "WorkerListView",
    "WorkerView",
)


class BaseRQView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff


class BackgroundQueueListView(TableMixin, BaseRQView):
    table = tables.BackgroundQueueTable

    def get(self, request):
        data = get_statistics(run_maintenance_tasks=True)["queues"]
        table = self.get_table(data, request, bulk_actions=False)

        return render(request, "core/task/rq_queue_list.html", {"table": table})


class BackgroundTaskListView(TableMixin, BaseRQView):
    table = tables.BackgroundTaskTable

    def get_table_data(self, request, queue, status):
        jobs = []

        if status == JobStatus.QUEUED:
            return queue.get_jobs()

        # For other statuses, determine the registry to list (or raise a 404 for
        # invalid statuses)
        try:
            registry_cls = {
                JobStatus.STARTED: StartedJobRegistry,
                JobStatus.DEFERRED: DeferredJobRegistry,
                JobStatus.FINISHED: FinishedJobRegistry,
                JobStatus.FAILED: FailedJobRegistry,
                JobStatus.SCHEDULED: ScheduledJobRegistry,
            }[status]
        except KeyError as e:
            raise Http404 from e
        registry = registry_cls(queue.name, queue.connection)

        job_ids = registry.get_job_ids()
        if status != JobStatus.DEFERRED:
            jobs = get_jobs(queue, job_ids, registry)
        else:
            # Deferred jobs require special handling
            for job_id in job_ids:
                with contextlib.suppress(NoSuchJobError):
                    jobs.append(
                        RQ_Job.fetch(
                            job_id,
                            connection=queue.connection,
                            serializer=queue.serializer,
                        )
                    )

        if jobs and status == JobStatus.SCHEDULED:
            for job in jobs:
                job.scheduled_at = registry.get_scheduled_time(job)

        return jobs

    def get(self, request, queue_index, status):
        queue = get_queue_by_index(queue_index)
        data = self.get_table_data(request, queue, status)
        table = self.get_table(data, request, False)

        return render(
            request,
            "core/task/rq_task_list.html",
            {"table": table, "queue": queue, "status": status},
        )


class BackgroundTaskView(BaseRQView):
    def get(self, request, job_id):
        # All the RQ queues should use the same connection
        config = QUEUES_LIST[0]
        try:
            job = RQ_Job.fetch(
                job_id,
                connection=get_redis_connection(config["connection_config"]),
            )
        except NoSuchJobError as e:
            raise Http404(f"Job {job_id} not found") from e

        queue_index = QUEUES_MAP[job.origin]
        queue = get_queue_by_index(queue_index)

        try:
            exc_info = job._exc_info
        except AttributeError:
            exc_info = None

        return render(
            request,
            "core/task/rq_task.html",
            {
                "queue": queue,
                "job": job,
                "queue_index": queue_index,
                "dependency_id": job._dependency_id,
                "exc_info": exc_info,
            },
        )


class WorkerListView(TableMixin, BaseRQView):
    table = tables.WorkerTable

    def get_table_data(self, request, queue):
        clean_worker_registry(queue)
        all_workers = Worker.all(queue.connection)
        return [worker for worker in all_workers if queue.name in worker.queue_names()]

    def get(self, request, queue_index):
        queue = get_queue_by_index(queue_index)
        data = self.get_table_data(request, queue)

        table = self.get_table(data, request, False)

        return render(
            request, "core/task/worker_list.html", {"table": table, "queue": queue}
        )


class WorkerView(BaseRQView):
    def get(self, request, key):
        config = QUEUES_LIST[0]
        worker = Worker.find_by_key(
            f"rq:worker:{key}",
            connection=get_redis_connection(config["connection_config"]),
        )
        # Time is in microseconds, report it in milliseconds
        worker.total_working_time = worker.total_working_time / 1000

        return render(
            request,
            "core/task/worker.html",
            {
                "worker": worker,
                "job": worker.get_current_job(),
                "total_working_time": worker.total_working_time * 1000,
            },
        )
