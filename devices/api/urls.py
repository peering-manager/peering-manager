from rest_framework import routers

from . import views


class DevicesRootView(routers.APIRootView):
    """
    Devices API root view
    """

    def get_view_name(self):
        return "Devices"


router = routers.DefaultRouter()
router.APIRootView = DevicesRootView

router.register("platforms", views.PlatformViewSet)

app_name = "devices-api"
urlpatterns = router.urls
