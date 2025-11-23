from django.urls import include, path

from utils.urls import get_model_urls

from . import views  # noqa: F401

app_name = "peering"
urlpatterns = [
    path(
        "autonomous-systems/",
        include(
            get_model_urls(
                app_label="peering", model_name="autonomoussystem", detail=False
            )
        ),
    ),
    path(
        "autonomous-systems/<int:pk>/",
        include(get_model_urls(app_label="peering", model_name="autonomoussystem")),
    ),
    path(
        "bgp-groups/",
        include(
            get_model_urls(app_label="peering", model_name="bgpgroup", detail=False)
        ),
    ),
    path(
        "bgp-groups/<int:pk>/",
        include(get_model_urls(app_label="peering", model_name="bgpgroup")),
    ),
    path(
        "direct-peering-sessions/",
        include(
            get_model_urls(
                app_label="peering", model_name="directpeeringsession", detail=False
            )
        ),
    ),
    path(
        "direct-peering-sessions/<int:pk>/",
        include(get_model_urls(app_label="peering", model_name="directpeeringsession")),
    ),
    path(
        "internet-exchanges/",
        include(
            get_model_urls(
                app_label="peering", model_name="internetexchange", detail=False
            )
        ),
    ),
    path(
        "internet-exchanges/<int:pk>/",
        include(get_model_urls(app_label="peering", model_name="internetexchange")),
    ),
    path(
        "internet-exchange-peering-sessions/",
        include(
            get_model_urls(
                app_label="peering",
                model_name="internetexchangepeeringsession",
                detail=False,
            )
        ),
    ),
    path(
        "internet-exchange-peering-sessions/<int:pk>/",
        include(
            get_model_urls(
                app_label="peering", model_name="internetexchangepeeringsession"
            )
        ),
    ),
    path(
        "routing-policies/",
        include(
            get_model_urls(
                app_label="peering", model_name="routingpolicy", detail=False
            )
        ),
    ),
    path(
        "routing-policies/<int:pk>/",
        include(get_model_urls(app_label="peering", model_name="routingpolicy")),
    ),
]
