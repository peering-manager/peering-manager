from django.urls import path

from utils.views import ObjectChangeLog

from . import models, views

app_name = "devices"

urlpatterns = [
    # Platforms
    path("platforms/", views.PlatformList.as_view(), name="platform_list"),
    path("platforms/add/", views.PlatformAdd.as_view(), name="platform_add"),
    path(
        "platforms/<slug:slug>/edit/",
        views.PlatformEdit.as_view(),
        name="platform_edit",
    ),
    path(
        "platforms/<slug:slug>/changelog/",
        ObjectChangeLog.as_view(),
        name="platform_changelog",
        kwargs={"model": models.Platform},
    ),
    path(
        "platforms/<slug:slug>/delete/",
        views.PlatformDelete.as_view(),
        name="platform_delete",
    ),
    path(
        "platforms/delete/",
        views.PlatformBulkDelete.as_view(),
        name="platform_bulk_delete",
    ),
]
