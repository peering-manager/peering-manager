from rest_framework import routers

from . import views


class UsersRootView(routers.APIRootView):
    """
    Peering API root view
    """

    def get_view_name(self):
        return "Users"


router = routers.DefaultRouter()
router.APIRootView = UsersRootView

router.register("groups", views.GroupViewSet)
router.register("users", views.UserViewSet)

app_name = "users-api"
urlpatterns = router.urls
