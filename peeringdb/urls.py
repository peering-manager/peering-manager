from django.urls import path
from . import views

app_name = "peeringdb"

urlpatterns = [
    # PeeringDB Cache
    path("cache/", views.CacheManagementView.as_view(), name="cache_management"),
    path(
        "peer-records/edit/",
        views.PeerRecordBulkEdit.as_view(),
        name="peer_record_bulk_edit",
    ),
]
