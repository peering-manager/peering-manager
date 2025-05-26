from django.urls import include, path

from utils.urls import get_model_urls

from . import views  # noqa: F401

app_name = "devices"
urlpatterns = [
    path(
        "configurations/",
        include(
            get_model_urls(
                app_label="devices", model_name="configuration", detail=False
            )
        ),
    ),
    path(
        "configurations/<int:pk>/",
        include(get_model_urls(app_label="devices", model_name="configuration")),
    ),
    path(
        "platforms/",
        include(
            get_model_urls(app_label="devices", model_name="platform", detail=False)
        ),
    ),
    path(
        "platforms/<int:pk>/",
        include(get_model_urls(app_label="devices", model_name="platform")),
    ),
    path(
        "routers/",
        include(get_model_urls(app_label="devices", model_name="router", detail=False)),
    ),
    path(
        "routers/<int:pk>/",
        include(get_model_urls(app_label="devices", model_name="router")),
    ),
]
