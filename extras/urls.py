from django.urls import path

from utils.views import ObjectChangeLog

from . import models, views

app_name = "extras"

urlpatterns = [
    path("ix-api/", views.IXAPIListView.as_view(), name="ixapi_list"),
    path("ix-api/add/", views.IXAPIAddView.as_view(), name="ixapi_add"),
    path("ix-api/<int:pk>/", views.IXAPIView.as_view(), name="ixapi_view"),
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
    path("ripe-irr/", views.RipeIrrListView.as_view(), name="ripeirr_list"),
    path("ripe-irr/add/", views.RipeIrrAddView.as_view(), name="ripeirr_add"),
    path("ripe-irr/<int:pk>/", views.RipeIrrView.as_view(), name="ripeirr_details"),
    path(
        "ripe-irr/<int:pk>/edit/", views.RipeIrrEditView.as_view(), name="ripeirr_edit"
    ),
    path(
        "ripe-irr/<int:pk>/delete/",
        views.RipeIrrDeleteView.as_view(),
        name="ripeirr_delete",
    ),
    path(
        "ripe-irr/aut-num/<int:pk>/update/",
        views.RipeIrrUpdateEntityView.as_view(),
        name="ripeirr_update_entity",
    ),
    path(
        "ripe-irr/<int:pk>/changelog/",
        ObjectChangeLog.as_view(),
        name="ripeirr_changelog",
        kwargs={"model": models.RipeIrr},
    ),
    path("job-results/", views.JobResultListView.as_view(), name="jobresult_list"),
    path("job-results/<int:pk>/", views.JobResultView.as_view(), name="jobresult_view"),
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
