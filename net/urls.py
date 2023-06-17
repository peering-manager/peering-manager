from django.urls import path

from extras.views import ObjectChangeLog

from . import models, views

app_name = "net"

urlpatterns = [
    # Connections
    path("connections/", views.ConnectionList.as_view(), name="connection_list"),
    path(
        "connections/<int:pk>/", views.ConnectionView.as_view(), name="connection_view"
    ),
    path("connections/add/", views.ConnectionAdd.as_view(), name="connection_add"),
    path(
        "connections/<int:pk>/config-context/",
        views.ConnectionContext.as_view(),
        name="connection_configcontext",
    ),
    path(
        "connections/<int:pk>/changelog/",
        ObjectChangeLog.as_view(),
        name="connection_changelog",
        kwargs={"model": models.Connection},
    ),
    path(
        "connections/<int:pk>/delete/",
        views.ConnectionDelete.as_view(),
        name="connection_delete",
    ),
    path(
        "connections/<int:pk>/edit/",
        views.ConnectionEdit.as_view(),
        name="connection_edit",
    ),
    path(
        "connections/edit/",
        views.ConnectionBulkEdit.as_view(),
        name="connection_bulk_edit",
    ),
    path(
        "connections/delete/",
        views.ConnectionBulkDelete.as_view(),
        name="connection_bulk_delete",
    ),
]
