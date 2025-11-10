from rest_framework.routers import APIRootView

__all__ = ("PeeringDBRootView",)


class PeeringDBRootView(APIRootView):
    def get_view_name(self):
        return "PeeringDB"
