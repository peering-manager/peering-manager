from django.urls import path

from . import models, views

app_name = "net"

urlpatterns = [
    # Connections
    path("connections/add/", views.ConnectionAdd.as_view(), name="connection_add"),
]
