from django.urls import path

from peering_manager.views.generic import ObjectChangeLogView

from . import models, views

app_name = "net"

urlpatterns = [
    # BFD configurations
    path("bfd/", views.BFDList.as_view(), name="bfd_list"),
    path("bfd/<int:pk>/", views.BFDView.as_view(), name="bfd_view"),
    path("bfd/add/", views.BFDEdit.as_view(), name="bfd_add"),
    path(
        "bfd/<int:pk>/config-context/",
        views.BFDContext.as_view(),
        name="bfd_configcontext",
    ),
    path(
        "bfd/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="bfd_changelog",
        kwargs={"model": models.BFD},
    ),
    path("bfd/<int:pk>/delete/", views.BFDDelete.as_view(), name="bfd_delete"),
    path("bfd/<int:pk>/edit/", views.BFDEdit.as_view(), name="bfd_edit"),
    path("bfd/edit/", views.BFDBulkEdit.as_view(), name="bfd_bulk_edit"),
    path("bfd/delete/", views.BFDBulkDelete.as_view(), name="bfd_bulk_delete"),
    # Connections
    path("connections/", views.ConnectionList.as_view(), name="connection_list"),
    path(
        "connections/<int:pk>/", views.ConnectionView.as_view(), name="connection_view"
    ),
    path("connections/add/", views.ConnectionEdit.as_view(), name="connection_add"),
    path(
        "connections/<int:pk>/config-context/",
        views.ConnectionContext.as_view(),
        name="connection_configcontext",
    ),
    path(
        "connections/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
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
