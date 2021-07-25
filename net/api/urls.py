from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.NetRootView

router.register("connections", views.ConnectionViewSet)

app_name = "net-api"
urlpatterns = router.urls
