from django.urls import include, path

from utils.urls import get_model_urls

from . import views  # noqa: F401

app_name = "bgp"
urlpatterns = [
    # Communities
    path(
        "communities/",
        include(get_model_urls(app_label="bgp", model_name="community", detail=False)),
    ),
    path(
        "communities/<int:pk>/",
        include(get_model_urls(app_label="bgp", model_name="community")),
    ),
    # Relationships
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
