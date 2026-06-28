from rest_framework.routers import APIRootView

from .community import *
from .relationship import *
from .routing_policy import *


class BGPRootView(APIRootView):
    def get_view_name(self):
        return "BGP"
