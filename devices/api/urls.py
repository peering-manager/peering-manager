from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.DevicesRootView

router.register("configurations", views.ConfigurationViewSet)
router.register("platforms", views.PlatformViewSet)
router.register("routers", views.RouterViewSet)

app_name = "devices-api"
urlpatterns = router.urls
