from django.urls import path

from utils.views import ObjectChangeLog

from . import models, views

app_name = "devices"

urlpatterns = [
    # Configurations
    path(
        "devices/configurations/",
        views.ConfigurationList.as_view(),
        name="configuration_list",
    ),
    path(
        "devices/configurations/add/",
        views.ConfigurationAdd.as_view(),
        name="configuration_add",
    ),
    path(
        "devices/configurations/<int:pk>/",
        views.ConfigurationDetails.as_view(),
        name="configuration_details",
    ),
    path(
        "devices/configurations/<int:pk>/edit/",
        views.ConfigurationEdit.as_view(),
        name="configuration_edit",
    ),
    path(
        "devices/configurations/<int:pk>/changelog/",
        ObjectChangeLog.as_view(),
        name="configuration_changelog",
        kwargs={"model": models.Configuration},
    ),
    path(
        "devices/configurations/<int:pk>/delete/",
        views.ConfigurationDelete.as_view(),
        name="configuration_delete",
    ),
    path(
        "devices/configurations/delete/",
        views.ConfigurationBulkDelete.as_view(),
        name="configuration_bulk_delete",
    ),
    # Platforms
    path("devices/platforms/", views.PlatformList.as_view(), name="platform_list"),
    path("devices/platforms/add/", views.PlatformAdd.as_view(), name="platform_add"),
    path(
        "devices/platforms/<int:pk>/edit/",
        views.PlatformEdit.as_view(),
        name="platform_edit",
    ),
    path(
        "devices/platforms/<int:pk>/changelog/",
        ObjectChangeLog.as_view(),
        name="platform_changelog",
        kwargs={"model": models.Platform},
    ),
    path(
        "devices/platforms/<int:pk>/delete/",
        views.PlatformDelete.as_view(),
        name="platform_delete",
    ),
    path(
        "devices/platforms/delete/",
        views.PlatformBulkDelete.as_view(),
        name="platform_bulk_delete",
    ),
]
