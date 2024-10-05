from django.urls import path

from peering_manager.views.generic import ObjectChangeLogView
from peering_manager.views.generic.feature_views import ObjectJobsView

from . import models, views

app_name = "core"

urlpatterns = [
    # Change logging
    path("changelog/", views.ObjectChangeList.as_view(), name="objectchange_list"),
    path(
        "changelog/<int:pk>/",
        views.ObjectChangeView.as_view(),
        name="objectchange_view",
    ),
    # Data sources
    path("data-sources/", views.DataSourceListView.as_view(), name="datasource_list"),
    path(
        "data-sources/add/", views.DataSourceEditView.as_view(), name="datasource_add"
    ),
    path(
        "data-sources/delete/",
        views.DataSourceBulkDeleteView.as_view(),
        name="datasource_bulk_delete",
    ),
    path(
        "data-sources/edit/",
        views.DataSourceBulkEdit.as_view(),
        name="datasource_bulk_edit",
    ),
    path(
        "data-sources/<int:pk>/", views.DataSourceView.as_view(), name="datasource_view"
    ),
    path(
        "data-sources/<int:pk>/files/",
        views.DataSourceFilesView.as_view(),
        name="datasource_files",
    ),
    path(
        "data-sources/<int:pk>/edit/",
        views.DataSourceEditView.as_view(),
        name="datasource_edit",
    ),
    path(
        "data-sources/<int:pk>/delete/",
        views.DataSourceDeleteView.as_view(),
        name="datasource_delete",
    ),
    path(
        "data-sources/<int:pk>/jobs/",
        ObjectJobsView.as_view(),
        name="datasource_jobs",
        kwargs={"model": models.DataSource},
    ),
    path(
        "data-sources/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="datasource_changelog",
        kwargs={"model": models.DataSource},
    ),
    # Data files
    path("data-files/", views.DataFileListView.as_view(), name="datafile_list"),
    path(
        "data-files/delete/",
        views.DataFileBulkDeleteView.as_view(),
        name="datafile_bulk_delete",
    ),
    path("data-files/<int:pk>/", views.DataFileView.as_view(), name="datafile_view"),
    path(
        "data-files/<int:pk>/delete/",
        views.DataFileDeleteView.as_view(),
        name="datafile_delete",
    ),
    # Jobs
    path("jobs/", views.JobListView.as_view(), name="job_list"),
    path("jobs/delete/", views.JobBulkDeleteView.as_view(), name="job_bulk_delete"),
    path("jobs/<int:pk>/", views.JobView.as_view(), name="job_view"),
    path("jobs/<int:pk>/delete/", views.JobDeleteView.as_view(), name="job_delete"),
    # Background Tasks
    path(
        "background-queues/",
        views.BackgroundQueueListView.as_view(),
        name="background_queue_list",
    ),
    path(
        "background-queues/<int:queue_index>/<str:status>/",
        views.BackgroundTaskListView.as_view(),
        name="background_task_list",
    ),
    path(
        "background-tasks/<str:job_id>/",
        views.BackgroundTaskView.as_view(),
        name="background_task",
    ),
    path(
        "background-workers/<int:queue_index>/",
        views.WorkerListView.as_view(),
        name="worker_list",
    ),
    path("background-workers/<str:key>/", views.WorkerView.as_view(), name="worker"),
    # System
    path("system/", views.SystemView.as_view(), name="system"),
]
