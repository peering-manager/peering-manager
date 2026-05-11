from rest_framework.routers import APIRootView

from .models import *


class PeeringRootView(APIRootView):
    def get_view_name(self):
        return "Peering"
