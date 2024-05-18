from django.urls import path

from peering_manager.views.generic import ObjectChangeLogView, ObjectJobsView

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
    # Routers
    path("routers/", views.RouterList.as_view(), name="router_list"),
    path("routers/add/", views.RouterEdit.as_view(), name="router_add"),
    path("routers/<int:pk>/", views.RouterView.as_view(), name="router_view"),
    path(
        "routers/<int:pk>/connections/",
        views.RouterConnections.as_view(),
        name="router_connections",
    ),
    path(
        "routers/<int:pk>/direct-peering-sessions/",
        views.RouterDirectPeeringSessions.as_view(),
        name="router_direct_peering_sessions",
    ),
    path(
        "routers/<int:pk>/ix-peering-sessions/",
        views.RouterInternetExchangesPeeringSessions.as_view(),
        name="router_internet_exchange_peering_sessions",
    ),
    path(
        "routers/<int:pk>/configuration/",
        views.RouterConfiguration.as_view(),
        name="router_configuration",
    ),
    path("routers/<int:pk>/edit/", views.RouterEdit.as_view(), name="router_edit"),
    path(
        "routers/<int:pk>/config-context/",
        views.RouterConfigContext.as_view(),
        name="router_configcontext",
    ),
    path(
        "routers/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="router_changelog",
        kwargs={"model": models.Router},
    ),
    path(
        "routers/<int:pk>/jobs/",
        ObjectJobsView.as_view(),
        name="router_jobs",
        kwargs={"model": models.Router},
    ),
    path(
        "routers/<int:pk>/delete/", views.RouterDelete.as_view(), name="router_delete"
    ),
    path(
        "routers/delete/", views.RouterBulkDelete.as_view(), name="router_bulk_delete"
    ),
    path("routers/edit/", views.RouterBulkEdit.as_view(), name="router_bulk_edit"),
]
