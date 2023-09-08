from django.urls import path

from peering_manager.views.generic import ObjectChangeLogView

from . import models, views

app_name = "bgp"

urlpatterns = [
    # Relationships
    path("relationships/", views.RelationshipList.as_view(), name="relationship_list"),
    path(
        "relationships/add/",
        views.RelationshipEdit.as_view(),
        name="relationship_add",
    ),
    path(
        "relationships/<int:pk>/",
        views.RelationshipView.as_view(),
        name="relationship_view",
    ),
    path(
        "relationships/<int:pk>/edit/",
        views.RelationshipEdit.as_view(),
        name="relationship_edit",
    ),
    path(
        "relationships/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="relationship_changelog",
        kwargs={"model": models.Relationship},
    ),
    path(
        "relationships/<int:pk>/delete/",
        views.RelationshipDelete.as_view(),
        name="relationship_delete",
    ),
    path(
        "relationships/delete/",
        views.RelationshipBulkDelete.as_view(),
        name="relationship_bulk_delete",
    ),
]
