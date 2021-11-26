from django.urls import path

from utils.views import ObjectChangeLog

from . import models, views

app_name = "bgp"

urlpatterns = [
    # Relationships
    path(
        "bgp/relationships/", views.RelationshipList.as_view(), name="relationship_list"
    ),
    path(
        "bgp/relationships/add/",
        views.RelationshipAdd.as_view(),
        name="relationship_add",
    ),
    path(
        "bgp/relationships/<int:pk>/",
        views.RelationshipDetails.as_view(),
        name="relationship_details",
    ),
    path(
        "bgp/relationships/<int:pk>/edit/",
        views.RelationshipEdit.as_view(),
        name="relationship_edit",
    ),
    path(
        "bgp/relationships/<int:pk>/changelog/",
        ObjectChangeLog.as_view(),
        name="relationship_changelog",
        kwargs={"model": models.Relationship},
    ),
    path(
        "bgp/relationships/<int:pk>/delete/",
        views.RelationshipDelete.as_view(),
        name="relationship_delete",
    ),
    path(
        "bgp/relationships/delete/",
        views.RelationshipBulkDelete.as_view(),
        name="relationship_bulk_delete",
    ),
]
