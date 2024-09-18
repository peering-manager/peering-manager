from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.NetRootView

router.register("bfd", views.BFDViewSet)
router.register("connections", views.ConnectionViewSet)

app_name = "net-api"
urlpatterns = router.urls
