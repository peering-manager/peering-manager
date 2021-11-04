from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.DevicesRootView

router.register("platforms", views.PlatformViewSet)

app_name = "devices-api"
urlpatterns = router.urls
