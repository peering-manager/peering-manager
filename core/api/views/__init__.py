from rest_framework.routers import APIRootView

from .change_logging import *
from .data import *
from .jobs import *


class CoreRootView(APIRootView):
    """
    Core API root view.
    """

    def get_view_name(self):
        return "Core"
