from peering_manager.api import OrderedDefaultRouter

from . import views

router = OrderedDefaultRouter()
router.APIRootView = views.BGPRootView

router.register("relationships", views.RelationshipViewSet)

app_name = "bgp-api"
urlpatterns = router.urls
