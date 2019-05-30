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
]
