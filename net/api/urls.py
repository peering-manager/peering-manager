from rest_framework import routers

from . import views


class NetRootView(routers.APIRootView):
    def get_view_name(self):
        return "Net"


router = routers.DefaultRouter()
router.APIRootView = NetRootView

router.register("connections", views.ConnectionViewSet)

app_name = "net-api"
urlpatterns = router.urls
