from django.urls import path

from . import views

app_name = "peeringdb"

urlpatterns = [
    # PeeringDB Cache
    path("cache/", views.CacheManagementView.as_view(), name="cache_management"),
    # Provisioning
    path("available-ixp-peers/", views.AvailableIXPPeers.as_view(), name="ixp_peers"),
]
