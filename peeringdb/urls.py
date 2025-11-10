from django.urls import include, path

from utils.urls import get_model_urls

from . import views

app_name = "peeringdb"

urlpatterns = [
    # Local cache
    path("cache/", views.CacheManagementView.as_view(), name="cache_management"),
    # Provisioning
    path("available-ixp-peers/", views.AvailableIXPPeers.as_view(), name="ixp_peers"),
    path("email-network/", views.EmailNetwork.as_view(), name="email_network"),
    # Hidden peers
    path(
        "hidden-peers/",
        include(
            get_model_urls(app_label="peeringdb", model_name="hiddenpeer", detail=False)
        ),
    ),
    path(
        "hidden-peers/<int:pk>/",
        include(get_model_urls(app_label="peeringdb", model_name="hiddenpeer")),
    ),
]
