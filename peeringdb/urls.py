from django.urls import path

from . import views

app_name = "peeringdb"

urlpatterns = [
    # PeeringDB Cache
    path(
        "peeringdb/cache/", views.CacheManagementView.as_view(), name="cache_management"
    ),
]
