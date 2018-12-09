from django.conf.urls import url

from . import views

app_name = "utils"
urlpatterns = [
    # Change logging
    url(r"^changelog/$", views.ObjectChangeList.as_view(), name="object_change_list"),
    url(
        r"^changelog/(?P<pk>\d+)/$",
        views.ObjectChangeView.as_view(),
        name="object_change_details",
    ),
]
