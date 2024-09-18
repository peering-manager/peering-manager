from rest_framework.routers import APIRootView

from .bfd import *
from .connections import *


class NetRootView(APIRootView):
    def get_view_name(self):
        return "Network"
