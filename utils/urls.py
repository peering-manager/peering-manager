from django.urls import path

from . import views

app_name = "utils"
urlpatterns = [
    # Change logging
    path("changelog/", views.ObjectChangeList.as_view(), name="objectchange_list"),
    path(
        "changelog/<int:pk>/",
        views.ObjectChangeDetails.as_view(),
        name="objectchange_details",
    ),
    # Tags
    path("tags/", views.TagList.as_view(), name="tag_list"),
    path("tags/add/", views.TagAdd.as_view(), name="tag_add"),
    path("tags/edit/", views.TagBulkEdit.as_view(), name="tag_bulk_edit"),
    path("tags/delete/", views.TagBulkDelete.as_view(), name="tag_bulk_delete"),
    path("tags/<int:pk>/", views.TagDetails.as_view(), name="tag_details"),
    path("tags/<int:pk>/edit/", views.TagEdit.as_view(), name="tag_edit"),
    path("tags/<int:pk>/delete/", views.TagDelete.as_view(), name="tag_delete"),
]
