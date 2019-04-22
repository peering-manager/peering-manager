from django.conf.urls import url
from . import views

app_name = "peeringdb"

urlpatterns = [
    # PeeringDB Cache
    url(r"^cache/$", views.CacheManagementView.as_view(), name="cache_management")
]
