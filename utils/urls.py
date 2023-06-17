from django.urls import path

from . import views

app_name = "utils"
urlpatterns = [
    # Change logging
    path("changelog/", views.ObjectChangeList.as_view(), name="objectchange_list"),
    path(
        "changelog/<int:pk>/",
        views.ObjectChangeView.as_view(),
        name="objectchange_view",
    ),
]
