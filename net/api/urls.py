from rest_framework import routers


class NetRootView(routers.APIRootView):
    def get_view_name(self):
        return "Net"


router = routers.DefaultRouter()
router.APIRootView = NetRootView

app_name = "net-api"
urlpatterns = router.urls
