from django.urls import include, path

from utils.urls import get_model_urls

from . import views  # noqa: F401

app_name = "bgp"
urlpatterns = [
    path(
        "relationships/",
        include(
            get_model_urls(app_label="bgp", model_name="relationship", detail=False)
        ),
    ),
    path(
        "relationships/<int:pk>/",
        include(get_model_urls(app_label="bgp", model_name="relationship")),
    ),
]
