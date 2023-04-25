from rest_framework.routers import APIRootView


class CoreRootView(APIRootView):
    """
    Core API root view.
    """

    def get_view_name(self):
        return "Core"
