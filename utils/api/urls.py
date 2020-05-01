from rest_framework import routers

from . import views


class UtilsRootView(routers.APIRootView):
    """
    Peering API root view
    """

    def get_view_name(self):
        return "Utils"


router = routers.DefaultRouter()
router.APIRootView = UtilsRootView

router.register("tags", views.TagViewSet)

app_name = "utils-api"
urlpatterns = router.urls
