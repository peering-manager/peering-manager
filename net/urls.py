from django.urls import path

from utils.views import ObjectChangeLog

from . import models, views

app_name = "net"

urlpatterns = [
    # Connections
    path(
        "connections/<int:pk>/",
        views.ConnectionDetails.as_view(),
        name="connection_details",
    ),
    path("connections/add/", views.ConnectionAdd.as_view(), name="connection_add"),
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
]
