from django.urls import include, path

from utils.urls import get_model_urls

from . import views  # noqa: F401

app_name = "extras"
urlpatterns = [
    path(
        "config-contexts/",
        include(
            get_model_urls(app_label="extras", model_name="configcontext", detail=False)
        ),
    ),
    path(
        "config-contexts/<int:pk>/",
        include(get_model_urls(app_label="extras", model_name="configcontext")),
    ),
    path(
        "config-context-assignments/",
        include(
            get_model_urls(
                app_label="extras", model_name="configcontextassignment", detail=False
            )
        ),
    ),
    path(
        "config-context-assignments/<int:pk>/",
        include(
            get_model_urls(app_label="extras", model_name="configcontextassignment")
        ),
    ),
    path(
        "export-templates/",
        include(
            get_model_urls(
                app_label="extras", model_name="exporttemplate", detail=False
            )
        ),
    ),
    path(
        "export-templates/<int:pk>/",
        include(get_model_urls(app_label="extras", model_name="exporttemplate")),
    ),
    path(
        "ix-api/",
        include(get_model_urls(app_label="extras", model_name="ixapi", detail=False)),
    ),
    path(
        "ix-api/<int:pk>/",
        include(get_model_urls(app_label="extras", model_name="ixapi")),
    ),
    path(
        "journal-entries/",
        include(
            get_model_urls(app_label="extras", model_name="journalentry", detail=False)
        ),
    ),
    path(
        "journal-entries/<int:pk>/",
        include(get_model_urls(app_label="extras", model_name="journalentry")),
    ),
    path(
        "tags/",
        include(get_model_urls(app_label="extras", model_name="tag", detail=False)),
    ),
    path(
        "tags/<int:pk>/", include(get_model_urls(app_label="extras", model_name="tag"))
    ),
    path(
        "webhooks/",
        include(get_model_urls(app_label="extras", model_name="webhook", detail=False)),
    ),
    path(
        "webhooks/<int:pk>/",
        include(get_model_urls(app_label="extras", model_name="webhook")),
    ),
]
