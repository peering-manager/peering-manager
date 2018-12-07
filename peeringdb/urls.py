from django.conf.urls import url
from . import views

app_name = "peeringdb"

urlpatterns = [
    # PeeringDB Cache
    url(r"^cache/$", views.CacheManagementView.as_view(), name="cache_management"),
    url(r"^cache/build/$", views.BuildCacheView.as_view(), name="build_cache"),
    url(r"^cache/clear/$", views.ClearCacheView.as_view(), name="clear_cache"),
    url(r"^cache/index/$", views.IndexPeerRecords.as_view(), name="index_peer_records"),
]
