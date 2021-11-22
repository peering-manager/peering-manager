from django.urls import path

from utils.views import ObjectChangeLog

from . import models, views

app_name = "extras"

urlpatterns = [
    path("ix-api/", views.IXAPIListView.as_view(), name="ixapi_list"),
    path("ix-api/add/", views.IXAPIAddView.as_view(), name="ixapi_add"),
    path("ix-api/<int:pk>/", views.IXAPIView.as_view(), name="ixapi_details"),
    path("ix-api/<int:pk>/edit/", views.IXAPIEditView.as_view(), name="ixapi_edit"),
    path(
        "ix-api/<int:pk>/delete/", views.IXAPIDeleteView.as_view(), name="ixapi_delete"
    ),
    path(
        "ix-api/<int:pk>/changelog/",
        ObjectChangeLog.as_view(),
        name="ixapi_changelog",
        kwargs={"model": models.IXAPI},
    ),
    path("job-results/", views.JobResultListView.as_view(), name="jobresult_list"),
    path(
        "job-results/<int:pk>/",
        views.JobResultView.as_view(),
        name="jobresult_details",
    ),
    path(
        "job-results/delete/",
        views.JobResultBulkDeleteView.as_view(),
        name="jobresult_bulk_delete",
    ),
    path(
        "job-results/<int:pk>/delete/",
        views.JobResultDeleteView.as_view(),
        name="jobresult_delete",
    ),
]
