from django.conf.urls import re_path

from . import views

app_name = "utils"
urlpatterns = [
    # Change logging
    re_path(
        r"^changelog/$", views.ObjectChangeList.as_view(), name="object_change_list"
    ),
    re_path(
        r"^changelog/(?P<pk>\d+)/$",
        views.ObjectChangeDetails.as_view(),
        name="object_change_details",
    ),
    # Tags
    re_path(r"^tags/$", views.TagList.as_view(), name="tag_list"),
    re_path(r"^tags/add/$", views.TagAdd.as_view(), name="tag_add"),
    re_path(r"^tags/edit/$", views.TagBulkEdit.as_view(), name="tag_bulk_edit"),
    re_path(r"^tags/delete/$", views.TagBulkDelete.as_view(), name="tag_bulk_delete"),
    re_path(
        r"^tags/(?P<slug>[\w-]+)/$", views.TagDetails.as_view(), name="tag_details"
    ),
    re_path(r"^tags/(?P<slug>[\w-]+)/edit/$", views.TagEdit.as_view(), name="tag_edit"),
    re_path(
        r"^tags/(?P<slug>[\w-]+)/delete/$", views.TagDelete.as_view(), name="tag_delete"
    ),
]
