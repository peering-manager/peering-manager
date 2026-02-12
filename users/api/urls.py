from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.UsersRootView

router.register("groups", views.GroupViewSet)
router.register("users", views.UserViewSet)
router.register("token-permissions", views.TokenObjectPermissionViewSet)
router.register("userpref", views.UserPreferencesViewSet, basename="userpref")

app_name = "users-api"
urlpatterns = router.urls
