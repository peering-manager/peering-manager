from django.urls import path

from . import views

app_name = "peeringdb"

urlpatterns = [
    # Local cache
    path("cache/", views.CacheManagementView.as_view(), name="cache_management"),
    # Provisioning
    path("available-ixp-peers/", views.AvailableIXPPeers.as_view(), name="ixp_peers"),
    path("email-network/", views.EmailNetwork.as_view(), name="email_network"),
]
