from django.urls import include, path

from utils.urls import get_model_urls

from . import views  # noqa: F401

app_name = "net"
urlpatterns = [
    path(
        "bfd/",
        include(get_model_urls(app_label="net", model_name="bfd", detail=False)),
    ),
    path(
        "bfd/<int:pk>/",
        include(get_model_urls(app_label="net", model_name="bfd")),
    ),
    path(
        "connections/",
        include(get_model_urls(app_label="net", model_name="connection", detail=False)),
    ),
    path(
        "connections/<int:pk>/",
        include(get_model_urls(app_label="net", model_name="connection")),
    ),
]
