from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.UsersRootView

router.register("groups", views.GroupViewSet)
router.register("users", views.UserViewSet)

app_name = "users-api"
urlpatterns = router.urls
