from django.urls import path

from peering_manager.views.generic import ObjectChangeLogView

from . import models, views

app_name = "core"

urlpatterns = [
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
        "data-sources/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="datasource_changelog",
        kwargs={"model": models.DataSource},
    ),
    path(
        "data-sources/<int:pk>/delete/",
        views.DataSourceDeleteView.as_view(),
        name="datasource_delete",
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
]
