from django.conf.urls import re_path
from . import views

app_name = "peeringdb"

urlpatterns = [
    # PeeringDB Cache
    re_path(r"^cache/$", views.CacheManagementView.as_view(), name="cache_management")
]
