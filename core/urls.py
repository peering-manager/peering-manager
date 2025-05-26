from django.urls import include, path

from utils.urls import get_model_urls

from . import views

app_name = "core"
urlpatterns = [
    path(
        "changelog/",
        include(
            get_model_urls(app_label="core", model_name="objectchange", detail=False)
        ),
    ),
    path(
        "changelog/<int:pk>/",
        include(get_model_urls(app_label="core", model_name="objectchange")),
    ),
    path(
        "data-sources/",
        include(
            get_model_urls(app_label="core", model_name="datasource", detail=False)
        ),
    ),
    path(
        "data-sources/<int:pk>/",
        include(get_model_urls(app_label="core", model_name="datasource")),
    ),
    path(
        "data-files/",
        include(get_model_urls(app_label="core", model_name="datafile", detail=False)),
    ),
    path(
        "data-files/<int:pk>/",
        include(get_model_urls(app_label="core", model_name="datafile")),
    ),
    path(
        "jobs/",
        include(get_model_urls(app_label="core", model_name="job", detail=False)),
    ),
    path(
        "jobs/<int:pk>/",
        include(get_model_urls(app_label="core", model_name="job")),
    ),
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
