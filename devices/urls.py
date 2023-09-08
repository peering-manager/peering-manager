from django.urls import path

from peering_manager.views.generic import ObjectChangeLogView

from . import models, views

app_name = "devices"

urlpatterns = [
    # Configurations
    path(
        "configurations/", views.ConfigurationList.as_view(), name="configuration_list"
    ),
    path(
        "configurations/add/",
        views.ConfigurationEdit.as_view(),
        name="configuration_add",
    ),
    path(
        "configurations/<int:pk>/",
        views.ConfigurationView.as_view(),
        name="configuration_view",
    ),
    path(
        "configurations/<int:pk>/edit/",
        views.ConfigurationEdit.as_view(),
        name="configuration_edit",
    ),
    path(
        "configurations/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="configuration_changelog",
        kwargs={"model": models.Configuration},
    ),
    path(
        "configurations/<int:pk>/delete/",
        views.ConfigurationDelete.as_view(),
        name="configuration_delete",
    ),
    path(
        "configurations/delete/",
        views.ConfigurationBulkDelete.as_view(),
        name="configuration_bulk_delete",
    ),
    # Platforms
    path("platforms/", views.PlatformList.as_view(), name="platform_list"),
    path("platforms/add/", views.PlatformEdit.as_view(), name="platform_add"),
    path(
        "platforms/<int:pk>/edit/", views.PlatformEdit.as_view(), name="platform_edit"
    ),
    path(
        "platforms/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="platform_changelog",
        kwargs={"model": models.Platform},
    ),
    path(
        "platforms/<int:pk>/delete/",
        views.PlatformDelete.as_view(),
        name="platform_delete",
    ),
    path(
        "platforms/delete/",
        views.PlatformBulkDelete.as_view(),
        name="platform_bulk_delete",
    ),
]
